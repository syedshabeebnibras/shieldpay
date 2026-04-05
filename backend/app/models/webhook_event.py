from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class WebhookEvent(Base):
    """Stores processed Stripe webhook event IDs for idempotency."""

    __tablename__ = "webhook_events"

    stripe_event_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), server_default="processed", nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
