import sqlite3
from contextlib import contextmanager
from .config import DATABASE_PATH


def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
  return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@contextmanager
def get_conn():
  conn = sqlite3.connect(DATABASE_PATH)
  conn.row_factory = dict_factory
  try:
    yield conn
    conn.commit()
  finally:
    conn.close()


def init_db() -> None:
  with get_conn() as conn:
    conn.executescript('''
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        openid TEXT NOT NULL UNIQUE,
        nickname TEXT NOT NULL,
        avatar_url TEXT,
        membership_status TEXT NOT NULL DEFAULT 'inactive',
        membership_expire_at TEXT,
        created_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS analysis_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        video_name TEXT NOT NULL,
        source_video_url TEXT NOT NULL,
        preview_image_url TEXT,
        processed_video_url TEXT,
        result_json TEXT,
        camera_view TEXT NOT NULL,
        status TEXT NOT NULL,
        error_message TEXT,
        is_paid_unlock INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        finished_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
      );
      CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        order_type TEXT NOT NULL,
        target_job_id INTEGER,
        amount REAL NOT NULL,
        status TEXT NOT NULL,
        plan_type TEXT,
        plan_days INTEGER,
        wechat_pay_order_no TEXT,
        paid_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(target_job_id) REFERENCES analysis_jobs(id)
      );
      CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        plan_type TEXT NOT NULL,
        start_at TEXT NOT NULL,
        expire_at TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
      );
    ''')
