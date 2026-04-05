import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class UserRole(str, enum.Enum):
    FREELANCER = "freelancer"
    CLIENT = "client"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    stripe_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    # Relationships
    projects_as_freelancer = relationship(
        "Project",
        back_populates="freelancer",
        foreign_keys="Project.freelancer_id",
    )
    projects_as_client = relationship(
        "Project",
        back_populates="client",
        foreign_keys="Project.client_id",
    )
    disputes_raised = relationship("Dispute", back_populates="raised_by_user")
    ratings_given = relationship(
        "Rating",
        back_populates="rated_by_user",
        foreign_keys="Rating.rated_by_id",
    )
