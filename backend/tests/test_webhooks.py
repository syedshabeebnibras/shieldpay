"""Webhook tests.

Strategy: We bypass Stripe signature verification by patching
stripe.Webhook.construct_event to return our crafted event dict directly.
This lets us test all handler logic without needing real Stripe signatures.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.milestone import Milestone, MilestoneStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.models.webhook_event import WebhookEvent


def _build_event(event_type: str, data_object: dict, event_id: str | None = None):
    """Build a Stripe-like event dict."""
    return {
        "id": event_id or f"evt_{uuid.uuid4().hex[:24]}",
        "type": event_type,
        "data": {"object": data_object},
    }


async def _create_funded_setup(
    client: AsyncClient, freelancer_token: str, mock_stripe
) -> tuple[str, str, str]:
    """Create a project + milestone + payment, return (project_id, milestone_id, pi_id).

    Simulates a payment being created but not yet succeeded.
    """
    # Create project
    resp = await client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {freelancer_token}"},
        json={
            "title": "Webhook Test Project",
            "client_email": "buyer@example.com",
            "milestones": [
                {"title": "Design Phase", "amount_cents": 10000},
            ],
        },
    )
    assert resp.status_code == 201, f"Project creation failed: {resp.text}"
    project = resp.json()
    project_id = project["id"]

    # Get milestone
    detail = await client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {freelancer_token}"},
    )
    milestone_id = detail.json()["milestones"][0]["id"]

    # Create a payment intent (mocked)
    mock_pi = MagicMock()
    mock_pi.id = f"pi_{uuid.uuid4().hex[:24]}"
    mock_pi.client_secret = f"{mock_pi.id}_secret_test"

    with patch(
        "app.api.payments.stripe_service.create_payment_intent",
        new_callable=AsyncMock,
        return_value=mock_pi,
    ):
        await client.post(f"/api/payments/create-intent/{milestone_id}")

    return project_id, milestone_id, mock_pi.id


# ═══════════════════════════════════════════════════════════════════════
# payment_intent.succeeded
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestPaymentIntentSucceeded:
    async def test_funds_milestone(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
        bypass_stripe_sig,
        db_engine,
    ):
        project_id, milestone_id, pi_id = await _create_funded_setup(
            client, freelancer_token, mock_stripe
        )

        event = _build_event(
            "payment_intent.succeeded",
            {
                "id": pi_id,
                "metadata": {
                    "project_id": project_id,
                    "milestone_id": milestone_id,
                },
                "latest_charge": "ch_test_abc",
            },
        )

        with bypass_stripe_sig(event):
            resp = await client.post(
                "/api/webhooks/stripe",
                content=b"raw_payload",
                headers={"stripe-signature": "t=1,v1=sig"},
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # Verify milestone is now funded
        detail = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        ms = detail.json()["milestones"][0]
        assert ms["status"] == "funded"
        assert ms["funded_at"] is not None

    async def test_ignores_event_without_milestone_id(
        self,
        client: AsyncClient,
        bypass_stripe_sig,
    ):
        event = _build_event(
            "payment_intent.succeeded",
            {"id": "pi_no_metadata", "metadata": {}},
        )
        with bypass_stripe_sig(event):
            resp = await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# payment_intent.payment_failed
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestPaymentIntentFailed:
    async def test_marks_payment_failed(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
        bypass_stripe_sig,
    ):
        _, milestone_id, pi_id = await _create_funded_setup(
            client, freelancer_token, mock_stripe
        )

        event = _build_event(
            "payment_intent.payment_failed",
            {
                "id": pi_id,
                "last_payment_error": {"message": "Card declined"},
            },
        )

        with bypass_stripe_sig(event):
            resp = await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )

        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# account.updated
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestAccountUpdated:
    async def test_verifies_user(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
        bypass_stripe_sig,
    ):
        # Get freelancer's stripe_account_id
        me = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        account_id = me.json()["stripe_account_id"]
        assert me.json()["is_verified"] is False

        event = _build_event(
            "account.updated",
            {
                "id": account_id,
                "charges_enabled": True,
                "payouts_enabled": True,
            },
        )

        with bypass_stripe_sig(event):
            resp = await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )

        assert resp.status_code == 200

        # Verify user is now verified
        me2 = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert me2.json()["is_verified"] is True

    async def test_ignores_incomplete_account(
        self,
        client: AsyncClient,
        bypass_stripe_sig,
    ):
        event = _build_event(
            "account.updated",
            {
                "id": "acct_not_ready",
                "charges_enabled": False,
                "payouts_enabled": False,
            },
        )
        with bypass_stripe_sig(event):
            resp = await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# charge.dispute.created
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestChargeDisputeCreated:
    async def test_creates_dispute_record(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
        bypass_stripe_sig,
    ):
        project_id, milestone_id, pi_id = await _create_funded_setup(
            client, freelancer_token, mock_stripe
        )

        # First fund the milestone so it has a charge
        fund_event = _build_event(
            "payment_intent.succeeded",
            {
                "id": pi_id,
                "metadata": {
                    "project_id": project_id,
                    "milestone_id": milestone_id,
                },
                "latest_charge": "ch_dispute_test",
            },
        )
        with bypass_stripe_sig(fund_event):
            await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )

        # Now create dispute
        dispute_event = _build_event(
            "charge.dispute.created",
            {
                "id": "dp_test_123",
                "charge": "ch_dispute_test",
                "payment_intent": pi_id,
                "reason": "fraudulent",
            },
        )

        with bypass_stripe_sig(dispute_event):
            resp = await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )

        assert resp.status_code == 200

        # Verify milestone is disputed
        detail = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        ms = detail.json()["milestones"][0]
        assert ms["status"] == "disputed"


# ═══════════════════════════════════════════════════════════════════════
# charge.refunded
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestChargeRefunded:
    async def test_full_refund_updates_records(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
        bypass_stripe_sig,
    ):
        project_id, milestone_id, pi_id = await _create_funded_setup(
            client, freelancer_token, mock_stripe
        )

        # Fund first
        fund_event = _build_event(
            "payment_intent.succeeded",
            {
                "id": pi_id,
                "metadata": {
                    "project_id": project_id,
                    "milestone_id": milestone_id,
                },
                "latest_charge": "ch_refund_test",
            },
        )
        with bypass_stripe_sig(fund_event):
            await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )

        # Now refund
        refund_event = _build_event(
            "charge.refunded",
            {
                "id": "ch_refund_test",
                "payment_intent": pi_id,
                "refunded": True,
                "amount_refunded": 10000,
                "amount": 10000,
            },
        )
        with bypass_stripe_sig(refund_event):
            resp = await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )

        assert resp.status_code == 200

        # Verify milestone is refunded
        detail = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        ms = detail.json()["milestones"][0]
        assert ms["status"] == "refunded"


# ═══════════════════════════════════════════════════════════════════════
# Idempotency
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestIdempotency:
    async def test_duplicate_event_is_skipped(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
        bypass_stripe_sig,
    ):
        project_id, milestone_id, pi_id = await _create_funded_setup(
            client, freelancer_token, mock_stripe
        )

        fixed_event_id = "evt_idempotency_test_12345"
        event = _build_event(
            "payment_intent.succeeded",
            {
                "id": pi_id,
                "metadata": {
                    "project_id": project_id,
                    "milestone_id": milestone_id,
                },
                "latest_charge": "ch_idemp",
            },
            event_id=fixed_event_id,
        )

        # First call — processes
        with bypass_stripe_sig(event):
            resp1 = await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )
        assert resp1.json()["status"] == "ok"

        # Second call — duplicate
        with bypass_stripe_sig(event):
            resp2 = await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )
        assert resp2.json()["status"] == "duplicate"


# ═══════════════════════════════════════════════════════════════════════
# Signature verification
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestSignatureVerification:
    async def test_missing_signature_header(self, client: AsyncClient):
        resp = await client.post(
            "/api/webhooks/stripe",
            content=b"{}",
        )
        assert resp.status_code == 400

    async def test_invalid_signature(self, client: AsyncClient):
        """Real construct_event should reject bad signatures."""
        resp = await client.post(
            "/api/webhooks/stripe",
            content=b"{}",
            headers={"stripe-signature": "t=1,v1=badsig"},
        )
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════════
# transfer.created (lighter — mostly logging)
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestTransferCreated:
    async def test_logs_transfer(
        self,
        client: AsyncClient,
        bypass_stripe_sig,
    ):
        event = _build_event(
            "transfer.created",
            {
                "id": "tr_test_789",
                "amount": 9650,
                "destination": "acct_freelancer",
                "transfer_group": "project_some-uuid",
            },
        )
        with bypass_stripe_sig(event):
            resp = await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )
        assert resp.status_code == 200
