import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class Project(Base):
    __tablename__ = "projects"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    client_email: Mapped[str] = mapped_column(String(255), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="projectstatus", values_callable=lambda e: [x.value for x in e]),
        server_default="draft",
        nullable=False,
    )
    total_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), server_default="usd", nullable=False)
    payment_token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    # Relationships
    freelancer = relationship(
        "User",
        back_populates="projects_as_freelancer",
        foreign_keys=[freelancer_id],
    )
    client = relationship(
        "User",
        back_populates="projects_as_client",
        foreign_keys=[client_id],
    )
    milestones = relationship(
        "Milestone",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Milestone.position",
    )
    ratings = relationship("Rating", back_populates="project")
