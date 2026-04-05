import argparse
import json
import sys
import time
import urllib.error
import urllib.request

def request_json(url: str, method: str = 'GET', payload: dict | None = None):
  data = json.dumps(payload).encode('utf-8') if payload is not None else None
  req = urllib.request.Request(url=url, method=method, data=data, headers={'Content-Type': 'application/json'})
  with urllib.request.urlopen(req, timeout=20) as resp:
    return json.loads(resp.read().decode('utf-8'))

def mock_result(job: dict) -> dict:
  if job.get('camera_view') == 'front_view':
    path_summary = 'club_path_slight_outside_in'
    insights = ['正面视角下挥杆轨迹基本稳定', '下杆路径略偏外到内', '建议继续优化击球区杆面控制']
  else:
    path_summary = 'club_path_shallow_downswing'
    insights = ['侧面视角下上杆节奏较稳定', '下杆角度偏浅，利于形成顺畅轨迹', '击球后收杆连贯性良好']
  return {
    'processed_video_url': f"{job['source_video_url']}?rendered=1",
    'preview_image_url': f"https://mock-storage.local/results/{job['id']}.jpg",
    'path_summary': path_summary,
    'tempo_score': min(68 + (job['id'] * 7) % 25, 99),
    'insights': insights,
    'checkpoints': [{'name': 'address', 'timestamp_ms': 0}, {'name': 'backswing_top', 'timestamp_ms': 820}, {'name': 'impact', 'timestamp_ms': 1360}, {'name': 'finish', 'timestamp_ms': 1880}],
  }

def run_once(api_base: str) -> int:
  jobs = request_json(f"{api_base}/api/internal/jobs/pending?limit=1")
  if not jobs:
    print('No pending jobs found.')
    return 0
  job = jobs[0]
  request_json(f"{api_base}/api/internal/jobs/{job['id']}/claim", method='POST', payload={})
  time.sleep(0.2)
  request_json(f"{api_base}/api/internal/jobs/{job['id']}/complete", method='POST', payload=mock_result(job))
  print(f"Processed job #{job['id']}")
  return 1

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
