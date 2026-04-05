from typing import Literal
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
  code: str | None = None
  nickname: str = '微信用户'
  avatar_url: str | None = None


class UploadTicketRequest(BaseModel):
  user_id: int
  filename: str


class CreateJobRequest(BaseModel):
  user_id: int
  video_name: str = Field(min_length=1)
  source_video_url: str = Field(min_length=1)
  camera_view: Literal['side_view', 'front_view'] = 'side_view'


class CreateOrderRequest(BaseModel):
  user_id: int
  order_type: Literal['single', 'subscription']
  amount: float = Field(gt=0)
  target_job_id: int | None = None
  plan_type: str | None = None
  plan_days: int | None = Field(default=None, gt=0)


class CompleteJobRequest(BaseModel):
  processed_video_url: str
  preview_image_url: str
  path_summary: str
  tempo_score: int = Field(ge=0, le=100)
  insights: list[str]
  checkpoints: list[dict]


class FailJobRequest(BaseModel):
  error_message: str = Field(min_length=1)
