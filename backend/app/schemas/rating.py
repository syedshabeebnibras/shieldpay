import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RatingCreate(BaseModel):
    score: int = Field(ge=1, le=5)
    comment: str | None = None


class RatingResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    rated_by_id: uuid.UUID
    rated_user_email: str
    score: int
    comment: str | None
    created_at: datetime


class ClientScoreResponse(BaseModel):
    email: str
    average_rating: float | None
    total_ratings: int
    total_projects: int
    total_amount_paid_cents: int
    avg_approval_days: float | None
    on_time_percentage: float | None
    dispute_rate: float | None
    trust_tier: str
