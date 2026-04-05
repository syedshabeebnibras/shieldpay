import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class MilestoneStatus(str, enum.Enum):
    DRAFT = "draft"
    FUNDED = "funded"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    APPROVED = "approved"
    DISPUTED = "disputed"
    RELEASED = "released"
    REFUNDED = "refunded"


class Milestone(Base):
    __tablename__ = "milestones"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[MilestoneStatus] = mapped_column(
        Enum(MilestoneStatus, name="milestonestatus", values_callable=lambda e: [x.value for x in e]),
        server_default="draft",
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Lifecycle timestamps
    funded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="milestones")
    payments = relationship(
        "Payment",
        back_populates="milestone",
        cascade="all, delete-orphan",
    )
    disputes = relationship(
        "Dispute",
        back_populates="milestone",
        cascade="all, delete-orphan",
    )
