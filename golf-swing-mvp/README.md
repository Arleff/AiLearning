# Golf Swing MVP

一个面向微信小程序的高尔夫挥杆分析 MVP 独立项目骨架，目标是尽快验证“上传挥杆视频 -> 生成挥杆轨迹 -> 支付解锁结果”的闭环。

## 目录结构

```text
golf-swing-mvp/
  apps/
    mini-golf/
  services/
    api/
    analysis-worker/
  docs/
    api.md
```

## 已实现的首版能力

- 小程序页面骨架：首页、上传、结果、历史、我的
- FastAPI 接口：模拟登录、上传凭证、任务创建、任务查询、订单创建、模拟支付、会员查询
- mock worker：拉取 pending 任务并回写示例分析结果

## 快速启动

### 1. 启动 API

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

### 2. 运行 worker

```bash
cd services/analysis-worker
python3 worker.py --api-base http://127.0.0.1:8000 --once
```

### 3. 导入微信开发者工具

导入目录：`apps/mini-golf`

启动前请把 `miniprogram/utils/api.js` 里的 `BASE_URL` 改成你可访问的 API 地址。
