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
- FastAPI 接口：
  - 模拟登录
  - 本地真实视频上传
  - 任务创建、任务查询
  - 订单创建、模拟支付、会员查询
- 最小真实分析 worker：
  - 读取真实视频
  - 基于帧差提取运动质心轨迹
  - 生成轨迹叠加视频与预览图
  - 回写结果 JSON

## 快速启动

### 1. 启动 API

```bash
cd services/api
python3 -m pip install --user -e .
python3 -m uvicorn app.main:app --reload --port 8000
```

### 2. 运行 worker

```bash
cd services/analysis-worker
python3 worker.py --api-base http://127.0.0.1:8000 --once
```

worker 会读取 `/api/uploads/video` 上传后的真实视频文件，并输出：

- `services/api/data/storage/results/job-<id>/trajectory.mp4`
- `services/api/data/storage/results/job-<id>/preview.jpg`

### 3. 导入微信开发者工具

导入目录：`apps/mini-golf`

启动前请把 `miniprogram/utils/api.js` 里的 `BASE_URL` 改成你可访问的 API 地址。

## 当前的真实分析方式

这个版本不是姿态估计模型，而是一个“真实视频最小版”：

- 接收真实挥杆视频
- 使用 OpenCV 逐帧读取
- 用背景建模 + 帧差检测主要运动区域
- 提取运动质心并绘制轨迹折线
- 输出叠加轨迹后的视频和预览图

它的目标是尽快验证“真实视频 -> 分析结果 -> 付费解锁”的闭环，而不是给出专业级挥杆诊断。
