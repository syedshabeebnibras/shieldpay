import logging
from typing import Sequence

from app.config import settings

logger = logging.getLogger(__name__)

FROM_EMAIL = "noreply@shieldpay.io"


async def _send_email(to: str, subject: str, html_content: str) -> None:
    """Send an email via SendGrid. Falls back to logging if not configured."""
    if not settings.sendgrid_api_key:
        logger.info(
            "[EMAIL] To: %s | Subject: %s\n%s",
            to,
            subject,
            html_content,
        )
        return

    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to,
        subject=subject,
        html_content=html_content,
    )
    try:
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        sg.send(message)
        logger.info("Sent email to %s: %s", to, subject)
    except Exception:
        logger.exception("Failed to send email to %s: %s", to, subject)


async def _send_to_many(
    recipients: Sequence[str], subject: str, html_content: str
) -> None:
    for email in recipients:
        await _send_email(email, subject, html_content)


# ---------------------------------------------------------------------------
# Project lifecycle
# ---------------------------------------------------------------------------


async def send_payment_link_email(
    client_email: str,
    freelancer_name: str,
    project_title: str,
    payment_link: str,
) -> None:
    await _send_email(
        to=client_email,
        subject=f"{freelancer_name} sent you a payment request — {project_title}",
        html_content=(
            f"<p>Hi,</p>"
            f"<p><strong>{freelancer_name}</strong> has created a project "
            f"<strong>{project_title}</strong> and is requesting payment.</p>"
            f'<p><a href="{payment_link}" style="background:#2563EB;color:#fff;'
            f'padding:10px 20px;border-radius:8px;text-decoration:none;'
            f'display:inline-block">Fund Milestones</a></p>'
            f"<p>Your payment is protected by ShieldPay escrow — funds are only "
            f"released when you approve each milestone.</p>"
            f"<p>— ShieldPay</p>"
        ),
    )


# ---------------------------------------------------------------------------
# Milestone lifecycle
# ---------------------------------------------------------------------------


async def send_milestone_funded(
    freelancer_email: str,
    project_title: str,
    milestone_title: str,
    amount_display: str,
) -> None:
    await _send_email(
        to=freelancer_email,
        subject=f"Milestone funded: {milestone_title} — {project_title}",
        html_content=(
            f"<p>Great news!</p>"
            f"<p>Your milestone <strong>{milestone_title}</strong> on project "
            f"<strong>{project_title}</strong> has been funded "
            f"(<strong>{amount_display}</strong>).</p>"
            f"<p>You can now start working. Once you're done, mark it as "
            f"delivered in your dashboard.</p>"
            f"<p>— ShieldPay</p>"
        ),
    )


async def send_milestone_delivered_email(
    client_email: str,
    freelancer_name: str,
    milestone_title: str,
    project_title: str,
    review_link: str,
) -> None:
    await _send_email(
        to=client_email,
        subject=f"Milestone delivered: {milestone_title} — {project_title}",
        html_content=(
            f"<p>Hi,</p>"
            f"<p><strong>{freelancer_name}</strong> has marked the milestone "
            f"<strong>{milestone_title}</strong> as delivered.</p>"
            f"<p>Please review the work and approve or request changes.</p>"
            f'<p><a href="{review_link}" style="background:#2563EB;color:#fff;'
            f'padding:10px 20px;border-radius:8px;text-decoration:none;'
            f'display:inline-block">Review Milestone</a></p>'
            f"<p>If you don't respond within 5 days, the payment will be "
            f"automatically released.</p>"
            f"<p>— ShieldPay</p>"
        ),
    )


async def send_payment_failed(
    client_email: str,
    project_title: str,
    milestone_title: str,
    error_message: str,
    payment_link: str,
) -> None:
    await _send_email(
        to=client_email,
        subject=f"Payment failed: {milestone_title} — {project_title}",
        html_content=(
            f"<p>Hi,</p>"
            f"<p>Your payment for milestone <strong>{milestone_title}</strong> "
            f"on project <strong>{project_title}</strong> has failed.</p>"
            f"<p>Reason: {error_message}</p>"
            f'<p><a href="{payment_link}" style="background:#2563EB;color:#fff;'
            f'padding:10px 20px;border-radius:8px;text-decoration:none;'
            f'display:inline-block">Try Again</a></p>'
            f"<p>— ShieldPay</p>"
        ),
    )


async def send_payment_released(
    freelancer_email: str,
    amount_display: str,
    milestone_title: str,
    project_title: str,
) -> None:
    await _send_email(
        to=freelancer_email,
        subject=f"Payment released: {amount_display} — {project_title}",
        html_content=(
            f"<p>You've been paid!</p>"
            f"<p><strong>{amount_display}</strong> for milestone "
            f"<strong>{milestone_title}</strong> on project "
            f"<strong>{project_title}</strong> has been released to your "
            f"connected Stripe account.</p>"
            f"<p>— ShieldPay</p>"
        ),
    )


# ---------------------------------------------------------------------------
# Disputes
# ---------------------------------------------------------------------------


async def send_dispute_opened(
    freelancer_email: str,
    client_email: str,
    milestone_title: str,
    project_title: str,
    reason: str,
) -> None:
    html = (
        f"<p>A dispute has been opened on milestone "
        f"<strong>{milestone_title}</strong> (project: "
        f"<strong>{project_title}</strong>).</p>"
        f"<p><strong>Reason:</strong> {reason}</p>"
        f"<p>Our team will review the dispute and get back to both parties. "
        f"Funds for this milestone are frozen until the dispute is resolved.</p>"
        f"<p>— ShieldPay</p>"
    )
    await _send_to_many(
        recipients=[freelancer_email, client_email],
        subject=f"Dispute opened: {milestone_title} — {project_title}",
        html_content=html,
    )


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------


async def send_account_verified(email: str, full_name: str) -> None:
    await _send_email(
        to=email,
        subject="Your ShieldPay account is verified!",
        html_content=(
            f"<p>Hi {full_name},</p>"
            f"<p>Your Stripe account has been verified. You can now receive "
            f"payouts for completed milestones.</p>"
            f"<p>— ShieldPay</p>"
        ),
    )
