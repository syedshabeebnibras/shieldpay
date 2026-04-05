import pytest
from httpx import AsyncClient


async def _setup_project(client: AsyncClient, freelancer_token: str) -> dict:
    """Create a project and return project detail with milestones."""
    resp = await client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {freelancer_token}"},
        json={
            "title": "Dispute Test Project",
            "client_email": "client@test.com",
            "milestones": [
                {"title": "Phase 1", "amount_cents": 10000},
            ],
        },
    )
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    detail = await client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {freelancer_token}"},
    )
    return detail.json()


@pytest.mark.asyncio
class TestOpenDispute:
    async def test_open_dispute_on_funded_milestone(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
        bypass_stripe_sig,
    ):
        """Fund a milestone via webhook, then dispute it."""
        from unittest.mock import AsyncMock, MagicMock, patch
        import uuid

        project = await _setup_project(client, freelancer_token)
        milestone_id = project["milestones"][0]["id"]

        # Create payment intent (mocked)
        mock_pi = MagicMock()
        mock_pi.id = f"pi_{uuid.uuid4().hex[:24]}"
        mock_pi.client_secret = "secret"

        with patch(
            "app.api.payments.stripe_service.create_payment_intent",
            new_callable=AsyncMock,
            return_value=mock_pi,
        ):
            await client.post(f"/api/payments/create-intent/{milestone_id}")

        # Fund via webhook
        from tests.test_webhooks import _build_event

        event = _build_event(
            "payment_intent.succeeded",
            {
                "id": mock_pi.id,
                "metadata": {
                    "project_id": project["id"],
                    "milestone_id": milestone_id,
                },
                "latest_charge": "ch_test",
            },
        )
        with bypass_stripe_sig(event):
            await client.post(
                "/api/webhooks/stripe",
                content=b"x",
                headers={"stripe-signature": "t=1,v1=sig"},
            )

        # Now open dispute
        resp = await client.post(
            f"/api/disputes/milestones/{milestone_id}/dispute",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "reason": "The client is unresponsive and I need this resolved. "
                "There are issues with the scope and deliverables."
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "open"
        assert data["milestone_id"] == milestone_id

        # Verify milestone is now disputed
        detail = await client.get(
            f"/api/projects/{project['id']}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert detail.json()["milestones"][0]["status"] == "disputed"
        assert detail.json()["status"] == "disputed"

    async def test_dispute_reason_too_short(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
    ):
        project = await _setup_project(client, freelancer_token)
        milestone_id = project["milestones"][0]["id"]

        resp = await client.post(
            f"/api/disputes/milestones/{milestone_id}/dispute",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={"reason": "Too short"},
        )
        assert resp.status_code == 422  # Pydantic validation

    async def test_dispute_draft_milestone_rejected(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
    ):
        project = await _setup_project(client, freelancer_token)
        milestone_id = project["milestones"][0]["id"]

        resp = await client.post(
            f"/api/disputes/milestones/{milestone_id}/dispute",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "reason": "x" * 50,
            },
        )
        assert resp.status_code == 400
        assert "draft" in resp.json()["detail"].lower()

    async def test_unrelated_user_cannot_dispute(
        self,
        client: AsyncClient,
        freelancer_token: str,
        client_token: str,
        mock_stripe,
    ):
        # Create project with a different client email
        resp = await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Other Project",
                "client_email": "someone-else@example.com",
                "milestones": [{"title": "M1", "amount_cents": 1000}],
            },
        )
        project_id = resp.json()["id"]
        detail = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        milestone_id = detail.json()["milestones"][0]["id"]

        resp = await client.post(
            f"/api/disputes/milestones/{milestone_id}/dispute",
            headers={"Authorization": f"Bearer {client_token}"},
            json={"reason": "x" * 50},
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestListDisputes:
    async def test_list_own_disputes(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
    ):
        resp = await client.get(
            "/api/disputes/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
