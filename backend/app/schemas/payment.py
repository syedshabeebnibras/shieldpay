import uuid
from datetime import datetime

from pydantic import BaseModel, computed_field

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    milestone_id: uuid.UUID


class PaymentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    milestone_id: uuid.UUID
    stripe_payment_intent_id: str
    stripe_charge_id: str | None
    amount_cents: int
    currency: str
    status: PaymentStatus
    client_email: str
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime | None

    @computed_field
    @property
    def amount_dollars(self) -> float:
        return self.amount_cents / 100


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
