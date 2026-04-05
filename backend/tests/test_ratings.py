import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRateClient:
    async def test_cannot_rate_non_completed_project(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
    ):
        # Create a draft project
        resp = await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Rating Test",
                "client_email": "buyer@example.com",
                "milestones": [{"title": "M1", "amount_cents": 5000}],
            },
        )
        project_id = resp.json()["id"]

        rate_resp = await client.post(
            f"/api/ratings/projects/{project_id}/rate",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={"score": 5, "comment": "Great client"},
        )
        assert rate_resp.status_code == 400
        assert "completion" in rate_resp.json()["detail"].lower()

    async def test_client_cannot_rate(
        self,
        client: AsyncClient,
        freelancer_token: str,
        client_token: str,
        mock_stripe,
    ):
        resp = await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Rating Test 2",
                "client_email": "client@test.com",
                "milestones": [{"title": "M1", "amount_cents": 5000}],
            },
        )
        project_id = resp.json()["id"]

        rate_resp = await client.post(
            f"/api/ratings/projects/{project_id}/rate",
            headers={"Authorization": f"Bearer {client_token}"},
            json={"score": 4},
        )
        assert rate_resp.status_code == 403

    async def test_invalid_score_rejected(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
    ):
        resp = await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Score Test",
                "client_email": "buyer@example.com",
                "milestones": [{"title": "M1", "amount_cents": 5000}],
            },
        )
        project_id = resp.json()["id"]

        for bad_score in [0, 6, -1]:
            rate_resp = await client.post(
                f"/api/ratings/projects/{project_id}/rate",
                headers={"Authorization": f"Bearer {freelancer_token}"},
                json={"score": bad_score},
            )
            assert rate_resp.status_code == 422


@pytest.mark.asyncio
class TestClientScore:
    async def test_score_for_new_client(
        self,
        client: AsyncClient,
    ):
        resp = await client.get(
            "/api/ratings/client-score/unknown@example.com",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["trust_tier"] == "new"
        assert data["total_projects"] == 0
        assert data["average_rating"] is None
        assert data["total_ratings"] == 0

    async def test_score_aggregation(
        self,
        client: AsyncClient,
        freelancer_token: str,
        mock_stripe,
    ):
        # Just check the endpoint works for an email with projects
        resp = await client.get(
            "/api/ratings/client-score/buyer@example.com",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "trust_tier" in data
        assert "average_rating" in data
        assert "on_time_percentage" in data
        assert "dispute_rate" in data
