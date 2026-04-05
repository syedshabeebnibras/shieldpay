import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, computed_field

from app.models.project import ProjectStatus
from app.schemas.milestone import MilestoneCreate, MilestoneResponse


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    client_email: EmailStr
    milestones: list[MilestoneCreate] = Field(min_length=1)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None


class ProjectResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    description: str | None
    freelancer_id: uuid.UUID
    client_email: str
    client_id: uuid.UUID | None
    status: ProjectStatus
    total_amount_cents: int
    currency: str
    payment_token: str
    created_at: datetime
    updated_at: datetime | None

    @computed_field
    @property
    def total_amount_dollars(self) -> float:
        return self.total_amount_cents / 100

    @computed_field
    @property
    def payment_link(self) -> str:
        from app.config import settings
        return f"{settings.frontend_url}/pay/{self.payment_token}"


class ProjectDetailResponse(ProjectResponse):
    milestones: list[MilestoneResponse] = []


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int


class CheckoutResponse(BaseModel):
    """Public checkout page data — no auth required."""
    model_config = {"from_attributes": True}

    project_title: str
    project_description: str | None
    freelancer_name: str
    client_email: str
    currency: str
    total_amount_cents: int
    milestones: list[MilestoneResponse]

    @computed_field
    @property
    def total_amount_dollars(self) -> float:
        return self.total_amount_cents / 100
