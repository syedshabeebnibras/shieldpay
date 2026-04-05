import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.dispute import DisputeStatus


class DisputeCreate(BaseModel):
    reason: str = Field(min_length=50)


class ResolutionType(str, Enum):
    FREELANCER = "freelancer"
    CLIENT = "client"
    SPLIT = "split"


class DisputeResolve(BaseModel):
    resolution: ResolutionType
    split_percentage: int = Field(default=0, ge=0, le=100)
    resolution_notes: str = Field(min_length=1)


class DisputeResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    milestone_id: uuid.UUID
    raised_by_id: uuid.UUID
    reason: str
    status: DisputeStatus
    resolution_notes: str | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime | None
