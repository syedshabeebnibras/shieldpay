import secrets
import uuid

from fastapi import APIRouter
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.config import settings
from app.models.milestone import Milestone, MilestoneStatus
from app.models.project import Project, ProjectStatus
from app.schemas.milestone import MilestoneResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services import notification_service
from app.utils.exceptions import BadRequestError, ForbiddenError, NotFoundError

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreate, current_user: CurrentUser, db: DbSession
) -> ProjectResponse:
    total = sum(m.amount_cents for m in body.milestones)
    payment_token = secrets.token_urlsafe(32)

    project = Project(
        title=body.title,
        description=body.description,
        freelancer_id=current_user.id,
        client_email=body.client_email,
        total_amount_cents=total,
        payment_token=payment_token,
    )
    db.add(project)
    await db.flush()

    for i, m in enumerate(body.milestones):
        milestone = Milestone(
            project_id=project.id,
            title=m.title,
            description=m.description,
            amount_cents=m.amount_cents,
            position=i,
            due_date=m.due_date,
        )
        db.add(milestone)

    await db.flush()
    await db.refresh(project)

    # Send email to client with payment link
    payment_link = f"{settings.frontend_url}/pay/{payment_token}"
    await notification_service.send_payment_link_email(
        client_email=body.client_email,
        freelancer_name=current_user.full_name,
        project_title=body.title,
        payment_link=payment_link,
    )

    return ProjectResponse.model_validate(project)


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    current_user: CurrentUser, db: DbSession
) -> list[ProjectResponse]:
    stmt = select(Project).where(
        or_(
            Project.freelancer_id == current_user.id,
            Project.client_id == current_user.id,
            Project.client_email == current_user.email,
        )
    ).order_by(Project.created_at.desc())

    result = await db.execute(stmt)
    projects = result.scalars().all()
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> ProjectDetailResponse:
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.milestones))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project not found")

    _check_project_access(project, current_user)

    milestones = [MilestoneResponse.model_validate(m) for m in project.milestones]
    resp = ProjectDetailResponse.model_validate(project)
    resp.milestones = milestones
    return resp


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectResponse:
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project not found")

    if project.freelancer_id != current_user.id:
        raise ForbiddenError("Only the project freelancer can update this project")

    if project.status != ProjectStatus.DRAFT:
        raise BadRequestError("Only draft projects can be updated")

    if body.title is not None:
        project.title = body.title
    if body.description is not None:
        project.description = body.description

    await db.flush()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> None:
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.milestones))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project not found")

    if project.freelancer_id != current_user.id:
        raise ForbiddenError("Only the project freelancer can delete this project")

    has_funded = any(
        m.status != MilestoneStatus.DRAFT for m in project.milestones
    )
    if has_funded:
        raise BadRequestError("Cannot delete project with funded milestones")

    await db.delete(project)
    await db.flush()


def _check_project_access(project: Project, user) -> None:
    if (
        project.freelancer_id != user.id
        and project.client_id != user.id
        and project.client_email != user.email
    ):
        raise ForbiddenError("You do not have access to this project")
