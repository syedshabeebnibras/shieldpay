import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, computed_field

from app.models.milestone import MilestoneStatus


class MilestoneCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    amount_cents: int = Field(gt=0)
    due_date: date | None = None


class MilestoneUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    status: MilestoneStatus | None = None
    due_date: date | None = None


class MilestoneResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    amount_cents: int
    position: int
    status: MilestoneStatus
    due_date: date | None
    funded_at: datetime | None
    delivered_at: datetime | None
    approved_at: datetime | None
    released_at: datetime | None
    stripe_payment_intent_id: str | None
    created_at: datetime
    updated_at: datetime | None

    @computed_field
    @property
    def amount_dollars(self) -> float:
        return self.amount_cents / 100
