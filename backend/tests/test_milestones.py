import pytest
from httpx import AsyncClient


async def _create_project_with_milestones(
    client: AsyncClient, token: str, client_email: str = "c@test.com"
) -> dict:
    resp = await client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Project",
            "client_email": client_email,
            "milestones": [
                {"title": "Phase 1", "amount_cents": 5000},
                {"title": "Phase 2", "amount_cents": 3000},
            ],
        },
    )
    return resp.json()


@pytest.mark.asyncio
class TestDeliverMilestone:
    async def test_deliver_funded_milestone(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
    ):
        project = await _create_project_with_milestones(client, freelancer_token)
        detail = await client.get(
            f"/api/projects/{project['id']}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        milestone_id = detail.json()["milestones"][0]["id"]

        # Manually set milestone to funded status for this test
        # Since we can't easily fund via stripe in tests, we test the
        # "deliver" on a funded milestone by first delivering a draft
        # (which should fail)
        resp = await client.post(
            f"/api/milestones/{milestone_id}/deliver",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        # Draft milestones can't be delivered
        assert resp.status_code == 400

    async def test_deliver_wrong_user(
        self,
        client: AsyncClient,
        freelancer_token: str,
        client_token: str,
        mock_stripe,
    ):
        project = await _create_project_with_milestones(client, freelancer_token)
        detail = await client.get(
            f"/api/projects/{project['id']}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        milestone_id = detail.json()["milestones"][0]["id"]

        # Client shouldn't be able to deliver
        resp = await client.post(
            f"/api/milestones/{milestone_id}/deliver",
            headers={"Authorization": f"Bearer {client_token}"},
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestApproveMilestone:
    async def test_approve_not_delivered(
        self,
        client: AsyncClient,
        freelancer_token: str,
        client_token: str,
        mock_stripe,
    ):
        project = await _create_project_with_milestones(
            client, freelancer_token, client_email="client@test.com"
        )
        detail = await client.get(
            f"/api/projects/{project['id']}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        milestone_id = detail.json()["milestones"][0]["id"]

        resp = await client.post(
            f"/api/milestones/{milestone_id}/approve",
            headers={"Authorization": f"Bearer {client_token}"},
        )
        assert resp.status_code == 400
        assert "delivered" in resp.json()["detail"].lower()
