import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import cv2
import numpy as np


ROOT_DIR = Path(__file__).resolve().parents[2]
UPLOAD_ROOT = ROOT_DIR / 'services' / 'api' / 'data'
RESULTS_ROOT = UPLOAD_ROOT / 'results'
RESULTS_ROOT.mkdir(parents=True, exist_ok=True)


def request_json(url: str, method: str = 'GET', payload: dict | None = None):
  data = json.dumps(payload).encode('utf-8') if payload is not None else None
  req = urllib.request.Request(url=url, method=method, data=data, headers={'Content-Type': 'application/json'})
  with urllib.request.urlopen(req, timeout=20) as resp:
    return json.loads(resp.read().decode('utf-8'))


def local_path_from_source(source_video_url: str) -> Path:
  parsed = urlparse(source_video_url)
  if parsed.scheme in ('', 'file'):
    return Path(parsed.path)
  if parsed.path.startswith('/storage/'):
    relative_path = parsed.path.removeprefix('/storage/')
    return UPLOAD_ROOT / relative_path
  raise ValueError(f'Unsupported source video url: {source_video_url}')


def compute_checkpoints(frame_count: int, fps: float) -> list[dict]:
  fps = fps or 15.0
  duration_ms = int(frame_count * 1000 / fps) if frame_count else 0
  return [
    {'name': 'address', 'timestamp_ms': 0},
    {'name': 'backswing_top', 'timestamp_ms': int(duration_ms * 0.35)},
    {'name': 'impact', 'timestamp_ms': int(duration_ms * 0.65)},
    {'name': 'finish', 'timestamp_ms': duration_ms},
  ]


def trajectory_summary(points: list[tuple[int, int]]) -> tuple[str, list[str], int]:
  if len(points) < 4:
    return 'motion_detected_too_short', ['视频运动信息较少，建议重新拍摄更完整挥杆过程'], 40

  xs = [point[0] for point in points]
  ys = [point[1] for point in points]
  dx = xs[-1] - xs[0]
  dy = ys[-1] - ys[0]
  slope = dy / dx if dx else 0.0
  travel = 0.0
  for index in range(1, len(points)):
    travel += math.dist(points[index - 1], points[index])

  if dx > 0 and abs(slope) < 0.45:
    path_summary = 'inside_to_square_path'
    insights = ['运动质心整体从后向前移动，挥杆路径较平顺', '轨迹横向延展明显，说明挥杆节奏较完整', '建议继续保持稳定拍摄机位，便于后续精细评估']
  elif slope < -0.45:
    path_summary = 'steep_downswing_path'
    insights = ['轨迹向下切入角度较明显，下杆偏陡', '建议关注杆头入球区前的路径稳定性', '可以增加侧面机位拍摄，辅助对比上杆与下杆平面']
  else:
    path_summary = 'shallow_arc_path'
    insights = ['轨迹呈现较明显弧线，挥杆连贯性不错', '整体运动范围充足，具备形成稳定节奏的基础', '建议继续优化击球区前后的加速衔接']

  tempo_score = int(max(45, min(95, 45 + travel / max(len(points), 1) * 2.2)))
  return path_summary, insights, tempo_score


def analyze_video(job: dict, api_base: str) -> dict:
  source_path = local_path_from_source(job['source_video_url'])
  if not source_path.exists():
    raise FileNotFoundError(f'Video not found: {source_path}')

  cap = cv2.VideoCapture(str(source_path))
  if not cap.isOpened():
    raise RuntimeError(f'Failed to open video: {source_path}')

  fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
  width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
  height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
  if width <= 0 or height <= 0:
    cap.release()
    raise RuntimeError('Invalid video size')

  output_dir = RESULTS_ROOT / f'job-{job["id"]}'
  output_dir.mkdir(parents=True, exist_ok=True)
  preview_path = output_dir / 'preview.jpg'
  processed_path = output_dir / 'trajectory.mp4'

  writer = cv2.VideoWriter(
    str(processed_path),
    cv2.VideoWriter_fourcc(*'mp4v'),
    fps,
    (width, height),
  )
  if not writer.isOpened():
    cap.release()
    raise RuntimeError(f'Failed to create output video: {processed_path}')

  points: list[tuple[int, int]] = []
  frame_count = 0
  background = None
  preview_frame = None

  try:
    while True:
      ok, frame = cap.read()
      if not ok:
        break
      frame_count += 1
      frame = cv2.resize(frame, (width, height))
      gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
      gray = cv2.GaussianBlur(gray, (11, 11), 0)

      if background is None:
        background = gray.astype('float32')
      cv2.accumulateWeighted(gray, background, 0.05)
      frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(background))
      _, thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)
      thresh = cv2.dilate(thresh, None, iterations=2)

      contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
      motion_center = None
      if contours:
        contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(contour) > 140:
          x, y, w, h = cv2.boundingRect(contour)
          motion_center = (x + w // 2, y + h // 2)
          points.append(motion_center)
          cv2.rectangle(frame, (x, y), (x + w, y + h), (28, 184, 65), 2)
          cv2.circle(frame, motion_center, 6, (0, 255, 255), -1)

      if len(points) > 1:
        pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], False, (255, 140, 0), 3)

      cv2.putText(frame, f'Frame: {frame_count}', (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
      cv2.putText(frame, f'Track points: {len(points)}', (16, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
      writer.write(frame)
      if preview_frame is None and (motion_center or frame_count > 5):
        preview_frame = frame.copy()
  finally:
    cap.release()
    writer.release()

  if preview_frame is None:
    preview_frame = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(preview_frame, 'No motion detected', (24, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

  cv2.imwrite(str(preview_path), preview_frame)
  path_summary, insights, tempo_score = trajectory_summary(points)

  processed_video_url = f'{api_base}/storage/results/job-{job["id"]}/trajectory.mp4'
  preview_image_url = f'{api_base}/storage/results/job-{job["id"]}/preview.jpg'
  return {
    'processed_video_url': processed_video_url,
    'preview_image_url': preview_image_url,
    'path_summary': path_summary,
    'tempo_score': tempo_score,
    'insights': insights,
    'checkpoints': compute_checkpoints(frame_count, fps),
  }

def run_once(api_base: str) -> int:
  jobs = request_json(f"{api_base}/api/internal/jobs/pending?limit=1")
  if not jobs:
    print('No pending jobs found.')
    return 0
  job = jobs[0]
  request_json(f"{api_base}/api/internal/jobs/{job['id']}/claim", method='POST', payload={})
  try:
    time.sleep(0.1)
    result = analyze_video(job, api_base.rstrip('/'))
    request_json(f"{api_base}/api/internal/jobs/{job['id']}/complete", method='POST', payload=result)
    print(f"Processed job #{job['id']}")
    return 1
  except Exception as exc:  # noqa: BLE001
    request_json(
      f"{api_base}/api/internal/jobs/{job['id']}/fail",
      method='POST',
      payload={'error_message': str(exc)},
    )
    raise

def main() -> int:
  parser = argparse.ArgumentParser(description='Golf swing mock analysis worker')
  parser.add_argument('--api-base', default='http://127.0.0.1:8000')
  parser.add_argument('--interval', type=float, default=3.0)
  parser.add_argument('--once', action='store_true')
  args = parser.parse_args()
  while True:
    try:
      processed = run_once(args.api_base.rstrip('/'))
      if args.once:
        return 0
      if processed == 0:
        time.sleep(args.interval)
    except urllib.error.HTTPError as exc:
      print(f'Worker HTTP error: {exc.code} {exc.reason}', file=sys.stderr)
      if args.once:
        return 1
      time.sleep(args.interval)
    except Exception as exc:
      print(f'Worker failed: {exc}', file=sys.stderr)
      if args.once:
        return 1
      time.sleep(args.interval)

if __name__ == '__main__':
  raise SystemExit(main())
