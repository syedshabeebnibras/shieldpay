import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.milestone import Milestone, MilestoneStatus
from app.models.payment import Payment, PaymentStatus
from app.models.project import Project, ProjectStatus
from app.services import stripe_service
from app.utils.exceptions import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)

PLATFORM_FEE_RATE = 0.035  # 3.5%


async def fund_milestone(
    db: AsyncSession, milestone_id, payment_intent_id: str
) -> None:
    """Called when payment succeeds. Mark milestone as funded."""
    result = await db.execute(
        select(Milestone).where(Milestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        logger.error("fund_milestone: milestone %s not found", milestone_id)
        return

    milestone.status = MilestoneStatus.FUNDED
    milestone.funded_at = datetime.now(timezone.utc)
    milestone.stripe_payment_intent_id = payment_intent_id

    # Update payment record
    pay_result = await db.execute(
        select(Payment).where(
            Payment.stripe_payment_intent_id == payment_intent_id
        )
    )
    payment = pay_result.scalar_one_or_none()
    if payment:
        payment.status = PaymentStatus.SUCCEEDED

    # If all milestones funded, activate project
    proj_result = await db.execute(
        select(Project)
        .options(selectinload(Project.milestones))
        .where(Project.id == milestone.project_id)
    )
    project = proj_result.scalar_one_or_none()
    if project and project.status == ProjectStatus.DRAFT:
        project.status = ProjectStatus.ACTIVE

    await db.flush()
    logger.info("Milestone %s funded via %s", milestone_id, payment_intent_id)


async def release_funds(db: AsyncSession, milestone_id) -> None:
    """Called when client approves. Transfer funds to freelancer."""
    result = await db.execute(
        select(Milestone)
        .options(
            selectinload(Milestone.project).selectinload(Project.freelancer)
        )
        .where(Milestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        raise NotFoundError("Milestone not found")

    if milestone.status != MilestoneStatus.APPROVED:
        raise BadRequestError("Milestone must be approved before releasing funds")

    project = milestone.project
    freelancer = project.freelancer

    if not freelancer.stripe_account_id:
        raise BadRequestError("Freelancer has no Stripe account")

    # Calculate platform fee
    platform_fee = int(milestone.amount_cents * PLATFORM_FEE_RATE)
    transfer_amount = milestone.amount_cents - platform_fee

    transfer = await stripe_service.create_transfer(
        amount_cents=transfer_amount,
        connected_account_id=freelancer.stripe_account_id,
        transfer_group=f"project_{project.id}",
    )

    milestone.status = MilestoneStatus.RELEASED
    milestone.released_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info(
        "Released %d cents to %s (fee: %d). Transfer: %s",
        transfer_amount,
        freelancer.stripe_account_id,
        platform_fee,
        transfer.id,
    )

    # Check if all milestones are released
    proj_result = await db.execute(
        select(Project)
        .options(selectinload(Project.milestones))
        .where(Project.id == project.id)
    )
    proj = proj_result.scalar_one()
    if all(m.status == MilestoneStatus.RELEASED for m in proj.milestones):
        proj.status = ProjectStatus.COMPLETED
        await db.flush()


async def refund_milestone(
    db: AsyncSession, milestone_id, amount_cents: int | None = None
) -> None:
    """Refund a milestone payment."""
    result = await db.execute(
        select(Milestone)
        .options(selectinload(Milestone.payments))
        .where(Milestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        raise NotFoundError("Milestone not found")

    if milestone.status not in (
        MilestoneStatus.FUNDED,
        MilestoneStatus.IN_PROGRESS,
        MilestoneStatus.DELIVERED,
        MilestoneStatus.DISPUTED,
    ):
        raise BadRequestError("Milestone cannot be refunded in current status")

    # Find the succeeded payment
    payment = next(
        (p for p in milestone.payments if p.status == PaymentStatus.SUCCEEDED),
        None,
    )
    if payment is None:
        raise BadRequestError("No successful payment found for this milestone")

    await stripe_service.create_refund(
        payment_intent_id=payment.stripe_payment_intent_id,
        amount_cents=amount_cents,
    )

    if amount_cents and amount_cents < payment.amount_cents:
        payment.status = PaymentStatus.PARTIALLY_REFUNDED
    else:
        payment.status = PaymentStatus.REFUNDED

    milestone.status = MilestoneStatus.REFUNDED
    await db.flush()

    logger.info("Refunded milestone %s", milestone_id)
