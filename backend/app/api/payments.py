import uuid

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.models.milestone import Milestone, MilestoneStatus
from app.models.payment import Payment
from app.models.project import Project
from app.schemas.milestone import MilestoneResponse
from app.schemas.payment import PaymentIntentResponse
from app.schemas.project import CheckoutResponse
from app.services import stripe_service
from app.utils.exceptions import BadRequestError, NotFoundError

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.get("/checkout/{payment_token}", response_model=CheckoutResponse)
async def get_checkout(payment_token: str, db: DbSession) -> CheckoutResponse:
    """Public endpoint — no auth. Returns project info for the payment page."""
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.milestones),
            selectinload(Project.freelancer),
        )
        .where(Project.payment_token == payment_token)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project not found")

    milestones = [MilestoneResponse.model_validate(m) for m in project.milestones]

    return CheckoutResponse(
        project_title=project.title,
        project_description=project.description,
        freelancer_name=project.freelancer.full_name,
        client_email=project.client_email,
        currency=project.currency,
        total_amount_cents=project.total_amount_cents,
        milestones=milestones,
    )


@router.post(
    "/create-intent/{milestone_id}", response_model=PaymentIntentResponse
)
async def create_payment_intent(
    milestone_id: uuid.UUID, db: DbSession
) -> PaymentIntentResponse:
    """Create a Stripe PaymentIntent for a milestone.

    Uses platform-level charge: funds go to the platform account first,
    then are transferred to the freelancer's connected account upon approval.
    """
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

    if milestone.status != MilestoneStatus.DRAFT:
        raise BadRequestError(
            f"Milestone is already in '{milestone.status.value}' status"
        )

    project = milestone.project
    freelancer = project.freelancer

    if not freelancer.stripe_account_id:
        raise BadRequestError("Freelancer has not completed Stripe onboarding")

    # Create PaymentIntent on platform — funds stay with us until release
    pi = await stripe_service.create_payment_intent(
        amount_cents=milestone.amount_cents,
        currency=project.currency,
        customer_id="",  # No customer for public checkout
        connected_account_id=freelancer.stripe_account_id,
        metadata={
            "project_id": str(project.id),
            "milestone_id": str(milestone.id),
            "freelancer_id": str(freelancer.id),
        },
    )

    # Store payment record
    payment = Payment(
        milestone_id=milestone.id,
        stripe_payment_intent_id=pi.id,
        amount_cents=milestone.amount_cents,
        currency=project.currency,
        client_email=project.client_email,
        metadata_json={
            "project_id": str(project.id),
            "milestone_id": str(milestone.id),
        },
    )
    db.add(payment)

    # Link PI to milestone
    milestone.stripe_payment_intent_id = pi.id
    await db.flush()

    return PaymentIntentResponse(
        client_secret=pi.client_secret,
        payment_intent_id=pi.id,
    )
