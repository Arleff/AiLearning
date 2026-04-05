# API 草案

基础路径：`/api`

## 用户与支付

- `POST /api/auth/mock-login`
- `POST /api/billing/orders`
- `POST /api/billing/orders/{order_id}/pay`
- `GET /api/billing/subscription/{user_id}`

## 视频上传与分析

- `POST /api/uploads/presign`
  - 旧的占位接口，保留兼容
- `POST /api/uploads/video`
  - `multipart/form-data`
  - 字段：
    - `user_id`
    - `file`
- `POST /api/analysis/jobs`
- `GET /api/analysis/jobs?user_id=1`
- `GET /api/analysis/jobs/{job_id}?user_id=1`

## Worker 内部接口

- `GET /api/internal/jobs/pending`
- `POST /api/internal/jobs/{job_id}/claim`
- `POST /api/internal/jobs/{job_id}/complete`
- `POST /api/internal/jobs/{job_id}/fail`

## 静态文件

- `GET /media/uploads/...`
  - 上传后的视频源文件
- `GET /media/results/...`
  - 轨迹叠加视频与预览图
