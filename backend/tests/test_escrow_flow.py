"""Integration test: full escrow lifecycle.

Covers: project creation -> payment -> fund via webhook -> deliver ->
approve -> release -> complete -> rate.
This tests the critical path through projects, milestones, payments,
escrow_service, webhooks, and ratings in one flow.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


def _build_event(event_type: str, data_object: dict, event_id: str | None = None):
    return {
        "id": event_id or f"evt_{uuid.uuid4().hex[:24]}",
        "type": event_type,
        "data": {"object": data_object},
    }


@pytest.mark.asyncio
class TestFullEscrowFlow:
    async def test_complete_project_lifecycle(
        self,
        client: AsyncClient,
        freelancer_token: str,
        client_token: str,
        mock_stripe,
        bypass_stripe_sig,
    ):
        # ── 1. Freelancer creates project ──────────────────────────────
        create_resp = await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Full Flow Test",
                "description": "End-to-end escrow test",
                "client_email": "client@test.com",
                "milestones": [
                    {"title": "Design", "amount_cents": 50000},
                    {"title": "Development", "amount_cents": 100000},
                ],
            },
        )
        assert create_resp.status_code == 201
        project = create_resp.json()
        assert project["status"] == "draft"
        assert project["total_amount_cents"] == 150000
        assert project["payment_link"]
        project_id = project["id"]

        # ── 2. Verify project detail has milestones ────────────────────
        detail_resp = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert len(detail["milestones"]) == 2
        m1_id = detail["milestones"][0]["id"]
        m2_id = detail["milestones"][1]["id"]

        # ── 3. Public checkout page works ──────────────────────────────
        checkout_resp = await client.get(
            f"/api/payments/checkout/{project['payment_token']}"
        )
        assert checkout_resp.status_code == 200
        assert checkout_resp.json()["freelancer_name"] == "Test Freelancer"
        assert len(checkout_resp.json()["milestones"]) == 2

        # ── 4. Create payment intent for milestone 1 ──────────────────
        mock_pi = MagicMock()
        mock_pi.id = f"pi_{uuid.uuid4().hex[:24]}"
        mock_pi.client_secret = f"{mock_pi.id}_secret"

        with patch(
            "app.api.payments.stripe_service.create_payment_intent",
            new_callable=AsyncMock,
            return_value=mock_pi,
        ):
            pi_resp = await client.post(
                f"/api/payments/create-intent/{m1_id}"
            )
            assert pi_resp.status_code == 200
            assert pi_resp.json()["client_secret"] == mock_pi.client_secret

        # ── 5. Simulate payment success via webhook ────────────────────
        event = _build_event(
            "payment_intent.succeeded",
            {
                "id": mock_pi.id,
                "metadata": {
                    "project_id": project_id,
                    "milestone_id": m1_id,
                },
                "latest_charge": "ch_flow_test",
            },
        )
        with bypass_stripe_sig(event):
            wh_resp = await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )
            assert wh_resp.status_code == 200

        # Verify milestone is funded and project is active
        detail2 = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert detail2.json()["status"] == "active"
        assert detail2.json()["milestones"][0]["status"] == "funded"
        assert detail2.json()["milestones"][0]["funded_at"] is not None

        # ── 6. Freelancer delivers milestone ───────────────────────────
        deliver_resp = await client.post(
            f"/api/milestones/{m1_id}/deliver",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert deliver_resp.status_code == 200
        assert deliver_resp.json()["status"] == "delivered"
        assert deliver_resp.json()["delivered_at"] is not None

        # ── 7. Client approves milestone — triggers payout ─────────────
        mock_transfer = MagicMock()
        mock_transfer.id = "tr_test_flow"

        with patch(
            "app.services.escrow_service.stripe_service.create_transfer",
            new_callable=AsyncMock,
            return_value=mock_transfer,
        ):
            approve_resp = await client.post(
                f"/api/milestones/{m1_id}/approve",
                headers={"Authorization": f"Bearer {client_token}"},
            )
            assert approve_resp.status_code == 200
            assert approve_resp.json()["status"] == "released"
            assert approve_resp.json()["released_at"] is not None

        # ── 8. Fund + deliver + approve milestone 2 ────────────────────
        mock_pi2 = MagicMock()
        mock_pi2.id = f"pi_{uuid.uuid4().hex[:24]}"
        mock_pi2.client_secret = f"{mock_pi2.id}_secret"

        with patch(
            "app.api.payments.stripe_service.create_payment_intent",
            new_callable=AsyncMock,
            return_value=mock_pi2,
        ):
            await client.post(f"/api/payments/create-intent/{m2_id}")

        event2 = _build_event(
            "payment_intent.succeeded",
            {
                "id": mock_pi2.id,
                "metadata": {"project_id": project_id, "milestone_id": m2_id},
                "latest_charge": "ch_flow_test2",
            },
        )
        with bypass_stripe_sig(event2):
            await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )

        await client.post(
            f"/api/milestones/{m2_id}/deliver",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )

        with patch(
            "app.services.escrow_service.stripe_service.create_transfer",
            new_callable=AsyncMock,
            return_value=mock_transfer,
        ):
            await client.post(
                f"/api/milestones/{m2_id}/approve",
                headers={"Authorization": f"Bearer {client_token}"},
            )

        # ── 9. Verify project is completed ─────────────────────────────
        final = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert final.json()["status"] == "completed"
        assert all(m["status"] == "released" for m in final.json()["milestones"])

        # ── 10. Freelancer rates client ────────────────────────────────
        rate_resp = await client.post(
            f"/api/ratings/projects/{project_id}/rate",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={"score": 5, "comment": "Excellent client, fast approvals!"},
        )
        assert rate_resp.status_code == 201
        assert rate_resp.json()["score"] == 5

        # ── 11. Check client reputation ────────────────────────────────
        score_resp = await client.get(
            "/api/ratings/client-score/client@test.com"
        )
        assert score_resp.status_code == 200
        score = score_resp.json()
        assert score["average_rating"] == 5.0
        assert score["total_ratings"] == 1
        assert score["total_projects"] >= 1

        # ── 12. Duplicate rating rejected ──────────────────────────────
        dup_resp = await client.post(
            f"/api/ratings/projects/{project_id}/rate",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={"score": 3},
        )
        assert dup_resp.status_code == 400

    async def test_client_can_view_and_approve_projects(
        self,
        client: AsyncClient,
        freelancer_token: str,
        client_token: str,
        mock_stripe,
    ):
        """Client can list projects where they're the client_email."""
        await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Client View Test",
                "client_email": "client@test.com",
                "milestones": [{"title": "M", "amount_cents": 1000}],
            },
        )

        # Client should see this project
        list_resp = await client.get(
            "/api/projects/",
            headers={"Authorization": f"Bearer {client_token}"},
        )
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1
        assert list_resp.json()[0]["title"] == "Client View Test"

    async def test_request_revision_flow(
        self,
        client: AsyncClient,
        freelancer_token: str,
        client_token: str,
        mock_stripe,
        bypass_stripe_sig,
    ):
        """Client requests revision, freelancer redelivers."""
        resp = await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Revision Test",
                "client_email": "client@test.com",
                "milestones": [{"title": "Work", "amount_cents": 5000}],
            },
        )
        project_id = resp.json()["id"]
        detail = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        m_id = detail.json()["milestones"][0]["id"]

        # Fund milestone
        mock_pi = MagicMock()
        mock_pi.id = f"pi_{uuid.uuid4().hex[:24]}"
        mock_pi.client_secret = "secret"
        with patch(
            "app.api.payments.stripe_service.create_payment_intent",
            new_callable=AsyncMock,
            return_value=mock_pi,
        ):
            await client.post(f"/api/payments/create-intent/{m_id}")

        event = _build_event(
            "payment_intent.succeeded",
            {"id": mock_pi.id, "metadata": {"project_id": project_id, "milestone_id": m_id}},
        )
        with bypass_stripe_sig(event):
            await client.post(
                "/api/webhooks/stripe", content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )

        # Deliver
        await client.post(
            f"/api/milestones/{m_id}/deliver",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )

        # Client requests revision
        rev_resp = await client.post(
            f"/api/milestones/{m_id}/request-revision",
            headers={"Authorization": f"Bearer {client_token}"},
        )
        assert rev_resp.status_code == 200
        assert rev_resp.json()["status"] == "in_progress"

        # Freelancer redelivers
        redeliver = await client.post(
            f"/api/milestones/{m_id}/deliver",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert redeliver.status_code == 200
        assert redeliver.json()["status"] == "delivered"
