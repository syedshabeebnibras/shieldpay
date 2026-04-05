import logging

import sentry_sdk
import stripe
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)

stripe.api_key = settings.stripe_secret_key


def _handle_stripe_error(e: stripe.error.StripeError, context: str) -> None:
    logger.error("Stripe error in %s: %s", context, str(e))
    sentry_sdk.capture_exception(e)
    if isinstance(e, stripe.error.CardError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Card error: {e.user_message}",
        )
    if isinstance(e, stripe.error.InvalidRequestError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        )
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Payment service error: {context}",
    )


async def create_connect_account(email: str) -> str:
    try:
        account = stripe.Account.create(
            type="express",
            email=email,
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
        )
        return account.id
    except stripe.error.StripeError as e:
        _handle_stripe_error(e, "create_connect_account")


async def create_account_link(
    account_id: str, return_url: str, refresh_url: str
) -> str:
    try:
        link = stripe.AccountLink.create(
            account=account_id,
            return_url=return_url,
            refresh_url=refresh_url,
            type="account_onboarding",
        )
        return link.url
    except stripe.error.StripeError as e:
        _handle_stripe_error(e, "create_account_link")


async def get_account_status(account_id: str) -> dict:
    try:
        account = stripe.Account.retrieve(account_id)
        return {
            "charges_enabled": account.charges_enabled,
            "payouts_enabled": account.payouts_enabled,
            "details_submitted": account.details_submitted,
        }
    except stripe.error.StripeError as e:
        _handle_stripe_error(e, "get_account_status")


async def create_customer(email: str) -> str:
    try:
        customer = stripe.Customer.create(email=email)
        return customer.id
    except stripe.error.StripeError as e:
        _handle_stripe_error(e, "create_customer")


async def create_payment_intent(
    amount_cents: int,
    currency: str,
    customer_id: str,
    connected_account_id: str,
    metadata: dict,
) -> stripe.PaymentIntent:
    try:
        params: dict = {
            "amount": amount_cents,
            "currency": currency,
            "metadata": metadata,
            "automatic_payment_methods": {"enabled": True},
        }
        if customer_id:
            params["customer"] = customer_id
        # Funds go to platform, we manually transfer on approval
        if connected_account_id:
            params["on_behalf_of"] = connected_account_id
        return stripe.PaymentIntent.create(**params)
    except stripe.error.StripeError as e:
        _handle_stripe_error(e, "create_payment_intent")


async def capture_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
    try:
        return stripe.PaymentIntent.capture(payment_intent_id)
    except stripe.error.StripeError as e:
        _handle_stripe_error(e, "capture_payment_intent")


async def create_transfer(
    amount_cents: int, connected_account_id: str, transfer_group: str
) -> stripe.Transfer:
    try:
        return stripe.Transfer.create(
            amount=amount_cents,
            currency="usd",
            destination=connected_account_id,
            transfer_group=transfer_group,
        )
    except stripe.error.StripeError as e:
        _handle_stripe_error(e, "create_transfer")


async def create_refund(
    payment_intent_id: str, amount_cents: int | None = None
) -> stripe.Refund:
    try:
        params: dict = {"payment_intent": payment_intent_id}
        if amount_cents is not None:
            params["amount"] = amount_cents
        return stripe.Refund.create(**params)
    except stripe.error.StripeError as e:
        _handle_stripe_error(e, "create_refund")
