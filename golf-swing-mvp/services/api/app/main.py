from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db
from .schemas import CompleteJobRequest, CreateJobRequest, CreateOrderRequest, FailJobRequest, LoginRequest, UploadTicketRequest
from .services import claim_job, complete_job, create_job, create_order, create_upload_ticket, fail_job, get_job, get_subscription, list_jobs, list_pending_jobs, mock_login, pay_order

app = FastAPI(title='Golf Swing MVP API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

@app.on_event('startup')
def startup_event() -> None:
  init_db()

@app.get('/health')
def health() -> dict:
  return {'status': 'ok'}

@app.post('/api/auth/mock-login')
def auth_mock_login(payload: LoginRequest) -> dict:
  return mock_login(payload.code, payload.nickname, payload.avatar_url)

@app.post('/api/uploads/presign')
def uploads_presign(payload: UploadTicketRequest) -> dict:
  return create_upload_ticket(payload.user_id, payload.filename)

@app.post('/api/analysis/jobs')
def analysis_create_job(payload: CreateJobRequest) -> dict:
  return create_job(payload.user_id, payload.video_name, payload.source_video_url, payload.camera_view)

@app.get('/api/analysis/jobs')
def analysis_list_jobs(user_id: int = Query(..., ge=1)) -> list[dict]:
  return list_jobs(user_id)

@app.get('/api/analysis/jobs/{job_id}')
def analysis_get_job(job_id: int, user_id: int = Query(..., ge=1)) -> dict:
  return get_job(job_id, user_id)

@app.post('/api/billing/orders')
def billing_create_order(payload: CreateOrderRequest) -> dict:
  return create_order(payload.model_dump())

@app.post('/api/billing/orders/{order_id}/pay')
def billing_pay_order(order_id: int) -> dict:
  return pay_order(order_id)

@app.get('/api/billing/subscription/{user_id}')
def billing_get_subscription(user_id: int) -> dict:
  return get_subscription(user_id)

@app.get('/api/internal/jobs/pending')
def internal_list_pending_jobs(limit: int = Query(1, ge=1, le=20)) -> list[dict]:
  return list_pending_jobs(limit)

@app.post('/api/internal/jobs/{job_id}/claim')
def internal_claim_job(job_id: int) -> dict:
  return claim_job(job_id)

@app.post('/api/internal/jobs/{job_id}/complete')
def internal_complete_job(job_id: int, payload: CompleteJobRequest) -> dict:
  return complete_job(job_id, payload.model_dump())

@app.post('/api/internal/jobs/{job_id}/fail')
def internal_fail_job(job_id: int, payload: FailJobRequest) -> dict:
  return fail_job(job_id, payload.error_message)
