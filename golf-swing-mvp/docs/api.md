# API 草案

基础路径：`/api`

- `POST /api/auth/mock-login`
- `POST /api/uploads/presign`
- `POST /api/analysis/jobs`
- `GET /api/analysis/jobs?user_id=1`
- `GET /api/analysis/jobs/{job_id}?user_id=1`
- `POST /api/billing/orders`
- `POST /api/billing/orders/{order_id}/pay`
- `GET /api/billing/subscription/{user_id}`
- `GET /api/internal/jobs/pending`
- `POST /api/internal/jobs/{job_id}/claim`
- `POST /api/internal/jobs/{job_id}/complete`
- `POST /api/internal/jobs/{job_id}/fail`
