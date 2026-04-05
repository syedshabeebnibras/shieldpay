import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.dispute import Dispute, DisputeStatus
from app.models.milestone import Milestone, MilestoneStatus
from app.models.project import Project, ProjectStatus
from app.schemas.dispute import DisputeCreate, DisputeResolve, DisputeResponse, ResolutionType
from app.services import escrow_service, notification_service
from app.utils.exceptions import BadRequestError, ForbiddenError, NotFoundError

router = APIRouter(prefix="/api/disputes", tags=["disputes"])


@router.post(
    "/milestones/{milestone_id}/dispute",
    response_model=DisputeResponse,
    status_code=201,
)
async def open_dispute(
    milestone_id: uuid.UUID,
    body: DisputeCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> DisputeResponse:
    result = await db.execute(
        select(Milestone)
        .options(
            selectinload(Milestone.project).selectinload(Project.freelancer),
            selectinload(Milestone.disputes),
        )
        .where(Milestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        raise NotFoundError("Milestone not found")

    project = milestone.project

    # Check the user is involved in the project
    is_freelancer = project.freelancer_id == current_user.id
    is_client = (
        project.client_id == current_user.id
        or project.client_email == current_user.email
    )
    if not (is_freelancer or is_client):
        raise ForbiddenError("You are not involved in this project")

    # Must be in a disputable state
    if milestone.status not in (
        MilestoneStatus.FUNDED,
        MilestoneStatus.IN_PROGRESS,
        MilestoneStatus.DELIVERED,
    ):
        raise BadRequestError(
            f"Cannot dispute a milestone in '{milestone.status.value}' status"
        )

    # Check no open dispute already exists
    open_disputes = [
        d for d in milestone.disputes if d.status == DisputeStatus.OPEN
    ]
    if open_disputes:
        raise BadRequestError("An open dispute already exists for this milestone")

    milestone.status = MilestoneStatus.DISPUTED
    project.status = ProjectStatus.DISPUTED

    dispute = Dispute(
        milestone_id=milestone.id,
        raised_by_id=current_user.id,
        reason=body.reason,
    )
    db.add(dispute)
    await db.flush()
    await db.refresh(dispute)

    # Notify both parties
    freelancer = project.freelancer
    await notification_service.send_dispute_opened(
        freelancer_email=freelancer.email,
        client_email=project.client_email,
        milestone_title=milestone.title,
        project_title=project.title,
        reason=body.reason,
    )

    return DisputeResponse.model_validate(dispute)


@router.get("/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(
    dispute_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DisputeResponse:
    result = await db.execute(
        select(Dispute)
        .options(
            selectinload(Dispute.milestone).selectinload(Milestone.project)
        )
        .where(Dispute.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    if dispute is None:
        raise NotFoundError("Dispute not found")

    project = dispute.milestone.project
    _check_dispute_access(project, current_user)

    return DisputeResponse.model_validate(dispute)


@router.post("/{dispute_id}/resolve", response_model=DisputeResponse)
async def resolve_dispute(
    dispute_id: uuid.UUID,
    body: DisputeResolve,
    admin_user: AdminUser,
    db: DbSession,
) -> DisputeResponse:
    result = await db.execute(
        select(Dispute)
        .options(
            selectinload(Dispute.milestone)
            .selectinload(Milestone.project)
            .selectinload(Project.freelancer)
        )
        .where(Dispute.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    if dispute is None:
        raise NotFoundError("Dispute not found")

    if dispute.status != DisputeStatus.OPEN:
        raise BadRequestError("Dispute is not open")

    milestone = dispute.milestone
    project = milestone.project
    now = datetime.now(timezone.utc)

    if body.resolution == ResolutionType.FREELANCER:
        dispute.status = DisputeStatus.RESOLVED_FREELANCER
        # Release full funds to freelancer
        milestone.status = MilestoneStatus.APPROVED
        milestone.approved_at = now
        await db.flush()
        await escrow_service.release_funds(db, milestone.id)

    elif body.resolution == ResolutionType.CLIENT:
        dispute.status = DisputeStatus.RESOLVED_CLIENT
        # Full refund to client
        await escrow_service.refund_milestone(db, milestone.id)

    elif body.resolution == ResolutionType.SPLIT:
        dispute.status = DisputeStatus.RESOLVED_SPLIT
        # Partial refund: split_percentage goes to client, rest to freelancer
        refund_amount = int(milestone.amount_cents * body.split_percentage / 100)
        if refund_amount > 0:
            await escrow_service.refund_milestone(
                db, milestone.id, amount_cents=refund_amount
            )
        # Transfer remainder to freelancer
        freelancer_amount = milestone.amount_cents - refund_amount
        if freelancer_amount > 0 and project.freelancer.stripe_account_id:
            from app.services import stripe_service

            await stripe_service.create_transfer(
                amount_cents=freelancer_amount,
                connected_account_id=project.freelancer.stripe_account_id,
                transfer_group=f"project_{project.id}",
            )
        milestone.status = MilestoneStatus.RELEASED
        milestone.released_at = now

    dispute.resolution_notes = body.resolution_notes
    dispute.resolved_at = now
    await db.flush()
    await db.refresh(dispute)

    return DisputeResponse.model_validate(dispute)


@router.get("/", response_model=list[DisputeResponse])
async def list_disputes(
    current_user: CurrentUser,
    db: DbSession,
) -> list[DisputeResponse]:
    from app.models.user import UserRole

    if current_user.role == UserRole.ADMIN:
        result = await db.execute(
            select(Dispute).order_by(Dispute.created_at.desc())
        )
    else:
        # Get disputes for projects the user is involved in
        result = await db.execute(
            select(Dispute)
            .join(Milestone, Dispute.milestone_id == Milestone.id)
            .join(Project, Milestone.project_id == Project.id)
            .where(
                or_(
                    Project.freelancer_id == current_user.id,
                    Project.client_id == current_user.id,
                    Project.client_email == current_user.email,
                )
            )
            .order_by(Dispute.created_at.desc())
        )

    disputes = result.scalars().all()
    return [DisputeResponse.model_validate(d) for d in disputes]


def _check_dispute_access(project: Project, user) -> None:
    from app.models.user import UserRole

    if user.role == UserRole.ADMIN:
        return
    if (
        project.freelancer_id != user.id
        and project.client_id != user.id
        and project.client_email != user.email
    ):
        raise ForbiddenError("You do not have access to this dispute")
