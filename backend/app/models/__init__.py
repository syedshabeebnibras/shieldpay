import uuid
from datetime import datetime

from sqlalchemy import DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )


# Import all models so Alembic's autogenerate detects them
from app.models.user import User  # noqa: E402, F401
from app.models.project import Project  # noqa: E402, F401
from app.models.milestone import Milestone  # noqa: E402, F401
from app.models.payment import Payment  # noqa: E402, F401
from app.models.dispute import Dispute  # noqa: E402, F401
from app.models.rating import Rating  # noqa: E402, F401
from app.models.webhook_event import WebhookEvent  # noqa: E402, F401
