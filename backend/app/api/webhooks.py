import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.config import settings
from app.models.dispute import Dispute, DisputeStatus
from app.models.milestone import Milestone, MilestoneStatus
from app.models.payment import Payment, PaymentStatus
from app.models.project import Project
from app.models.user import User
from app.models.webhook_event import WebhookEvent
from app.services import escrow_service, notification_service
from app.utils.exceptions import BadRequestError
from app.utils.rate_limit import WEBHOOK_LIMIT, limiter

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/stripe")
@limiter.limit(WEBHOOK_LIMIT)
async def stripe_webhook(request: Request, db: DbSession) -> dict:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise BadRequestError("Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise BadRequestError("Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise BadRequestError("Invalid signature")

    event_id: str = event["id"]
    event_type: str = event["type"]

    # ── Idempotency check ──────────────────────────────────────────────
    existing = await db.execute(
        select(WebhookEvent).where(WebhookEvent.stripe_event_id == event_id)
    )
    if existing.scalar_one_or_none() is not None:
        logger.info("Webhook %s already processed, skipping", event_id)
        return {"status": "duplicate"}

    # Record event before processing (mark in-progress)
    webhook_record = WebhookEvent(
        stripe_event_id=event_id,
        event_type=event_type,
        status="processing",
    )
    db.add(webhook_record)
    await db.flush()

    # ── Dispatch to handler ────────────────────────────────────��───────
    data = event["data"]["object"]
    logger.info("Webhook received: %s (event %s)", event_type, event_id)

    try:
        handler = EVENT_HANDLERS.get(event_type)
        if handler:
            await handler(data, db)
        else:
            logger.debug("Unhandled webhook event type: %s", event_type)

        webhook_record.status = "processed"
    except Exception as exc:
        logger.exception("Error processing webhook %s (%s)", event_id, event_type)
        webhook_record.status = "failed"
        webhook_record.error_message = str(exc)[:1000]

    await db.flush()
    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════════════════
# Event handlers
# ═══════════════════════════════════════════════════════════════════════


async def _handle_payment_intent_succeeded(
    data: dict, db: AsyncSession
) -> None:
    """Payment succeeded — fund the milestone and notify the freelancer."""
    payment_intent_id = data["id"]
    metadata = data.get("metadata", {})
    milestone_id = metadata.get("milestone_id")

    if not milestone_id:
        logger.warning(
            "payment_intent.succeeded %s has no milestone_id in metadata",
            payment_intent_id,
        )
        return

    # Fund the milestone via escrow service
    await escrow_service.fund_milestone(
        db=db,
        milestone_id=milestone_id,
        payment_intent_id=payment_intent_id,
    )

    # Store charge_id on payment record if present
    charges = data.get("latest_charge")
    if charges:
        pay_result = await db.execute(
            select(Payment).where(
                Payment.stripe_payment_intent_id == payment_intent_id
            )
        )
        payment = pay_result.scalar_one_or_none()
        if payment:
            payment.stripe_charge_id = charges

    # Send notification to freelancer
    result = await db.execute(
        select(Milestone)
        .options(
            selectinload(Milestone.project).selectinload(Project.freelancer)
        )
        .where(Milestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    if milestone:
        project = milestone.project
        freelancer = project.freelancer
        amount_display = f"${milestone.amount_cents / 100:,.2f}"
        await notification_service.send_milestone_funded(
            freelancer_email=freelancer.email,
            project_title=project.title,
            milestone_title=milestone.title,
            amount_display=amount_display,
        )

    logger.info(
        "payment_intent.succeeded: milestone %s funded via %s",
        milestone_id,
        payment_intent_id,
    )


async def _handle_payment_intent_failed(
    data: dict, db: AsyncSession
) -> None:
    """Payment failed — update record and notify client."""
    payment_intent_id = data["id"]
    error_info = data.get("last_payment_error", {})
    error_message = error_info.get("message", "Unknown error")

    logger.warning(
        "payment_intent.payment_failed: %s — %s",
        payment_intent_id,
        error_message,
    )

    # Update payment record
    pay_result = await db.execute(
        select(Payment).where(
            Payment.stripe_payment_intent_id == payment_intent_id
        )
    )
    payment = pay_result.scalar_one_or_none()
    if not payment:
        return

    payment.status = PaymentStatus.FAILED
    await db.flush()

    # Get milestone and project for notification
    result = await db.execute(
        select(Milestone)
        .options(selectinload(Milestone.project))
        .where(Milestone.id == payment.milestone_id)
    )
    milestone = result.scalar_one_or_none()
    if milestone:
        project = milestone.project
        payment_link = (
            f"{settings.frontend_url}/pay/{project.payment_token}"
        )
        await notification_service.send_payment_failed(
            client_email=project.client_email,
            project_title=project.title,
            milestone_title=milestone.title,
            error_message=error_message,
            payment_link=payment_link,
        )


async def _handle_transfer_created(data: dict, db: AsyncSession) -> None:
    """Transfer to freelancer's connected account was created."""
    transfer_id = data["id"]
    amount = data.get("amount", 0)
    destination = data.get("destination", "unknown")
    transfer_group = data.get("transfer_group", "")

    logger.info(
        "transfer.created: %s — %d cents to %s (group: %s)",
        transfer_id,
        amount,
        destination,
        transfer_group,
    )

    # If we can identify the milestone from transfer_group, send notification
    # transfer_group format: "project_{uuid}"
    if transfer_group.startswith("project_"):
        project_id = transfer_group.replace("project_", "")
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.freelancer), selectinload(Project.milestones))
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if project:
            # Find the most recently released milestone
            released = [
                m for m in project.milestones
                if m.status == MilestoneStatus.RELEASED
            ]
            if released:
                released.sort(key=lambda m: m.released_at or m.created_at, reverse=True)
                ms = released[0]
                amount_display = f"${(amount) / 100:,.2f}"
                await notification_service.send_payment_released(
                    freelancer_email=project.freelancer.email,
                    amount_display=amount_display,
                    milestone_title=ms.title,
                    project_title=project.title,
                )


async def _handle_account_updated(data: dict, db: AsyncSession) -> None:
    """Stripe Connect account updated — check verification status."""
    account_id = data.get("id", "")
    charges_enabled = data.get("charges_enabled", False)
    payouts_enabled = data.get("payouts_enabled", False)

    logger.info(
        "account.updated: %s — charges=%s, payouts=%s",
        account_id,
        charges_enabled,
        payouts_enabled,
    )

    if not (charges_enabled and payouts_enabled):
        return

    # Find user by stripe_account_id
    result = await db.execute(
        select(User).where(User.stripe_account_id == account_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        logger.warning("account.updated: no user with stripe_account_id %s", account_id)
        return

    if not user.is_verified:
        user.is_verified = True
        await db.flush()
        logger.info("User %s (%s) verified via account.updated", user.id, user.email)

        await notification_service.send_account_verified(
            email=user.email,
            full_name=user.full_name,
        )


async def _handle_charge_dispute_created(
    data: dict, db: AsyncSession
) -> None:
    """Stripe charge dispute — create Dispute record, freeze milestone."""
    charge_id = data.get("id", "")
    dispute_charge = data.get("charge", "")
    reason = data.get("reason", "unknown")

    logger.warning("charge.dispute.created: %s (charge: %s)", charge_id, dispute_charge)

    # Find payment by charge_id
    pay_result = await db.execute(
        select(Payment).where(Payment.stripe_charge_id == dispute_charge)
    )
    payment = pay_result.scalar_one_or_none()

    if payment is None:
        # Try by payment_intent
        payment_intent = data.get("payment_intent", "")
        if payment_intent:
            pay_result = await db.execute(
                select(Payment).where(
                    Payment.stripe_payment_intent_id == payment_intent
                )
            )
            payment = pay_result.scalar_one_or_none()

    if payment is None:
        logger.warning("charge.dispute.created: cannot find payment for dispute %s", charge_id)
        return

    # Load milestone + project + freelancer
    result = await db.execute(
        select(Milestone)
        .options(
            selectinload(Milestone.project).selectinload(Project.freelancer)
        )
        .where(Milestone.id == payment.milestone_id)
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        return

    project = milestone.project
    freelancer = project.freelancer

    # Set milestone to disputed
    milestone.status = MilestoneStatus.DISPUTED
    await db.flush()

    # Set project to disputed
    project.status = "disputed"
    await db.flush()

    # Create dispute record
    dispute = Dispute(
        milestone_id=milestone.id,
        raised_by_id=freelancer.id,  # system-initiated, attributed to freelancer side
        reason=f"Stripe dispute: {reason}",
        status=DisputeStatus.OPEN,
    )
    db.add(dispute)
    await db.flush()

    # Notify both parties
    await notification_service.send_dispute_opened(
        freelancer_email=freelancer.email,
        client_email=project.client_email,
        milestone_title=milestone.title,
        project_title=project.title,
        reason=f"Stripe dispute: {reason}",
    )

    logger.info(
        "Dispute created for milestone %s on project %s",
        milestone.id,
        project.id,
    )


async def _handle_charge_refunded(data: dict, db: AsyncSession) -> None:
    """Charge was refunded — update payment and milestone records."""
    charge_id = data.get("id", "")
    payment_intent_id = data.get("payment_intent", "")
    refunded = data.get("refunded", False)
    amount_refunded = data.get("amount_refunded", 0)
    amount_total = data.get("amount", 0)

    logger.info(
        "charge.refunded: %s (PI: %s) — refunded %d/%d",
        charge_id,
        payment_intent_id,
        amount_refunded,
        amount_total,
    )

    if not payment_intent_id:
        return

    pay_result = await db.execute(
        select(Payment).where(
            Payment.stripe_payment_intent_id == payment_intent_id
        )
    )
    payment = pay_result.scalar_one_or_none()
    if payment is None:
        return

    if refunded and amount_refunded >= amount_total:
        payment.status = PaymentStatus.REFUNDED
    else:
        payment.status = PaymentStatus.PARTIALLY_REFUNDED

    # Update milestone status
    result = await db.execute(
        select(Milestone).where(Milestone.id == payment.milestone_id)
    )
    milestone = result.scalar_one_or_none()
    if milestone and payment.status == PaymentStatus.REFUNDED:
        milestone.status = MilestoneStatus.REFUNDED

    await db.flush()


# ── Event handler registry ─────────────────────────────────────────────

EVENT_HANDLERS = {
    "payment_intent.succeeded": _handle_payment_intent_succeeded,
    "payment_intent.payment_failed": _handle_payment_intent_failed,
    "transfer.created": _handle_transfer_created,
    "account.updated": _handle_account_updated,
    "charge.dispute.created": _handle_charge_dispute_created,
    "charge.refunded": _handle_charge_refunded,
}
