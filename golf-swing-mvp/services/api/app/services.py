import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import HTTPException
from .db import get_conn


def now_iso() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_iso(value: str | None):
  return datetime.fromisoformat(value) if value else None


def ensure_user_exists(conn, user_id: int) -> dict:
  user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
  if not user:
    raise HTTPException(status_code=404, detail='用户不存在')
  return user


def refresh_membership(user_id: int) -> dict:
  with get_conn() as conn:
    user = ensure_user_exists(conn, user_id)
    expire_at = parse_iso(user.get('membership_expire_at'))
    active = bool(expire_at and expire_at > datetime.now(timezone.utc))
    conn.execute(
      'UPDATE users SET membership_status = ?, membership_expire_at = ? WHERE id = ?',
      ('active' if active else 'inactive', user.get('membership_expire_at') if active else None, user_id),
    )
    return conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()


def serialize_job(job: dict, user: dict) -> dict:
  accessible = bool(job['is_paid_unlock'] or user['membership_status'] == 'active')
  result_json = json.loads(job['result_json']) if job['result_json'] else None
  if not accessible:
    return {
      **job,
      'is_accessible': False,
      'processed_video_url': None,
      'result_json': result_json and {
        'path_summary': result_json.get('path_summary'),
        'tempo_score': None,
        'insights': ['支付后查看完整分析结果'],
        'checkpoints': result_json.get('checkpoints', []),
      },
    }
  return {**job, 'is_accessible': True, 'result_json': result_json}


def mock_login(code: str | None, nickname: str, avatar_url: str | None) -> dict:
  openid = code or f'mock-{uuid4().hex[:12]}'
  with get_conn() as conn:
    user = conn.execute('SELECT * FROM users WHERE openid = ?', (openid,)).fetchone()
    if user:
      return refresh_membership(user['id'])
    cursor = conn.execute(
      'INSERT INTO users (openid, nickname, avatar_url, membership_status, created_at) VALUES (?, ?, ?, ?, ?)',
      (openid, nickname, avatar_url, 'inactive', now_iso()),
    )
  return refresh_membership(cursor.lastrowid)


def create_upload_ticket(user_id: int, filename: str) -> dict:
  with get_conn() as conn:
    ensure_user_exists(conn, user_id)
  object_key = f'uploads/user-{user_id}/{uuid4().hex}-{filename}'
  return {'object_key': object_key, 'object_url': f'https://mock-storage.local/{object_key}', 'upload_method': 'PUT'}


def create_job(user_id: int, video_name: str, source_video_url: str, camera_view: str) -> dict:
  with get_conn() as conn:
    user = ensure_user_exists(conn, user_id)
    cursor = conn.execute(
      'INSERT INTO analysis_jobs (user_id, video_name, source_video_url, preview_image_url, processed_video_url, result_json, camera_view, status, error_message, is_paid_unlock, created_at, finished_at) VALUES (?, ?, ?, ?, NULL, NULL, ?, ?, NULL, 0, ?, NULL)',
      (user_id, video_name, source_video_url, f'https://mock-storage.local/previews/{uuid4().hex}.jpg', camera_view, 'pending', now_iso()),
    )
    job = conn.execute('SELECT * FROM analysis_jobs WHERE id = ?', (cursor.lastrowid,)).fetchone()
  return serialize_job(job, user)


def get_job(job_id: int, user_id: int) -> dict:
  user = refresh_membership(user_id)
  with get_conn() as conn:
    job = conn.execute('SELECT * FROM analysis_jobs WHERE id = ? AND user_id = ?', (job_id, user_id)).fetchone()
  if not job:
    raise HTTPException(status_code=404, detail='任务不存在')
  return serialize_job(job, user)


def list_jobs(user_id: int) -> list[dict]:
  user = refresh_membership(user_id)
  with get_conn() as conn:
    jobs = conn.execute('SELECT * FROM analysis_jobs WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
  return [serialize_job(job, user) for job in jobs]


def create_order(payload: dict) -> dict:
  with get_conn() as conn:
    ensure_user_exists(conn, payload['user_id'])
    if payload['order_type'] == 'single':
      if not payload.get('target_job_id'):
        raise HTTPException(status_code=400, detail='单次订单必须关联任务')
      job = conn.execute(
        'SELECT * FROM analysis_jobs WHERE id = ? AND user_id = ?',
        (payload['target_job_id'], payload['user_id']),
      ).fetchone()
      if not job:
        raise HTTPException(status_code=404, detail='目标任务不存在')
    cursor = conn.execute(
      'INSERT INTO orders (user_id, order_type, target_job_id, amount, status, plan_type, plan_days, wechat_pay_order_no, paid_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)',
      (payload['user_id'], payload['order_type'], payload.get('target_job_id'), payload['amount'], 'created', payload.get('plan_type'), payload.get('plan_days'), now_iso()),
    )
    return conn.execute('SELECT * FROM orders WHERE id = ?', (cursor.lastrowid,)).fetchone()


def pay_order(order_id: int) -> dict:
  paid_at = now_iso()
  with get_conn() as conn:
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
      raise HTTPException(status_code=404, detail='订单不存在')
    if order['status'] == 'paid':
      return order
    conn.execute(
      'UPDATE orders SET status = ?, wechat_pay_order_no = ?, paid_at = ? WHERE id = ?',
      ('paid', f'MOCK-{uuid4().hex[:12].upper()}', paid_at, order_id),
    )
    if order['order_type'] == 'single' and order['target_job_id']:
      conn.execute('UPDATE analysis_jobs SET is_paid_unlock = 1 WHERE id = ? AND user_id = ?', (order['target_job_id'], order['user_id']))
    if order['order_type'] == 'subscription':
      start_at = datetime.now(timezone.utc).replace(microsecond=0)
      expire_at = start_at + timedelta(days=order['plan_days'] or 30)
      conn.execute(
        'INSERT INTO subscriptions (user_id, plan_type, start_at, expire_at, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        (order['user_id'], order['plan_type'] or 'monthly', start_at.isoformat(), expire_at.isoformat(), 'active', paid_at),
      )
      conn.execute('UPDATE users SET membership_status = ?, membership_expire_at = ? WHERE id = ?', ('active', expire_at.isoformat(), order['user_id']))
    return conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()


def get_subscription(user_id: int) -> dict:
  user = refresh_membership(user_id)
  with get_conn() as conn:
    subscription = conn.execute('SELECT * FROM subscriptions WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,)).fetchone()
  return subscription or {'user_id': user_id, 'status': user['membership_status'], 'plan_type': None, 'expire_at': user['membership_expire_at']}


def list_pending_jobs(limit: int) -> list[dict]:
  with get_conn() as conn:
    return conn.execute("SELECT * FROM analysis_jobs WHERE status = 'pending' ORDER BY id ASC LIMIT ?", (limit,)).fetchall()


def claim_job(job_id: int) -> dict:
  with get_conn() as conn:
    job = conn.execute('SELECT * FROM analysis_jobs WHERE id = ?', (job_id,)).fetchone()
    if not job:
      raise HTTPException(status_code=404, detail='任务不存在')
    if job['status'] != 'pending':
      raise HTTPException(status_code=409, detail='任务不可抢占')
    conn.execute('UPDATE analysis_jobs SET status = ? WHERE id = ?', ('running', job_id))
    return conn.execute('SELECT * FROM analysis_jobs WHERE id = ?', (job_id,)).fetchone()


def complete_job(job_id: int, payload: dict) -> dict:
  result_json = json.dumps(
    {
      'path_summary': payload['path_summary'],
      'tempo_score': payload['tempo_score'],
      'insights': payload['insights'],
      'checkpoints': payload['checkpoints'],
    },
    ensure_ascii=False,
  )
  with get_conn() as conn:
    job = conn.execute('SELECT * FROM analysis_jobs WHERE id = ?', (job_id,)).fetchone()
    if not job:
      raise HTTPException(status_code=404, detail='任务不存在')
    conn.execute(
      'UPDATE analysis_jobs SET status = ?, processed_video_url = ?, preview_image_url = ?, result_json = ?, finished_at = ?, error_message = NULL WHERE id = ?',
      ('success', payload['processed_video_url'], payload['preview_image_url'], result_json, now_iso(), job_id),
    )
    return conn.execute('SELECT * FROM analysis_jobs WHERE id = ?', (job_id,)).fetchone()


def fail_job(job_id: int, error_message: str) -> dict:
  with get_conn() as conn:
    job = conn.execute('SELECT * FROM analysis_jobs WHERE id = ?', (job_id,)).fetchone()
    if not job:
      raise HTTPException(status_code=404, detail='任务不存在')
    conn.execute('UPDATE analysis_jobs SET status = ?, error_message = ?, finished_at = ? WHERE id = ?', ('failed', error_message, now_iso(), job_id))
    return conn.execute('SELECT * FROM analysis_jobs WHERE id = ?', (job_id,)).fetchone()
