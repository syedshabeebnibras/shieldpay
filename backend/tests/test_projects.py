import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreateProject:
    async def test_create_project(self, client: AsyncClient, freelancer_token: str, mock_stripe):
        resp = await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Website Redesign",
                "description": "Complete redesign",
                "client_email": "client@test.com",
                "milestones": [
                    {"title": "Design", "amount_cents": 50000},
                    {"title": "Development", "amount_cents": 100000},
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Website Redesign"
        assert data["total_amount_cents"] == 150000
        assert data["status"] == "draft"
        assert data["payment_token"]
        assert data["payment_link"]
        assert data["client_email"] == "client@test.com"

    async def test_create_project_no_milestones(
        self, client: AsyncClient, freelancer_token: str, mock_stripe
    ):
        resp = await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Test",
                "client_email": "client@test.com",
                "milestones": [],
            },
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestListProjects:
    async def test_list_as_freelancer(
        self, client: AsyncClient, freelancer_token: str, mock_stripe
    ):
        # Create two projects
        for title in ["Project A", "Project B"]:
            await client.post(
                "/api/projects/",
                headers={"Authorization": f"Bearer {freelancer_token}"},
                json={
                    "title": title,
                    "client_email": "c@test.com",
                    "milestones": [{"title": "M1", "amount_cents": 1000}],
                },
            )

        resp = await client.get(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2


@pytest.mark.asyncio
class TestGetProject:
    async def test_get_project_detail(
        self, client: AsyncClient, freelancer_token: str, mock_stripe
    ):
        create_resp = await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Detail Test",
                "client_email": "c@test.com",
                "milestones": [
                    {"title": "Phase 1", "amount_cents": 5000},
                    {"title": "Phase 2", "amount_cents": 3000},
                ],
            },
        )
        project_id = create_resp.json()["id"]

        resp = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["milestones"]) == 2
        assert data["milestones"][0]["title"] == "Phase 1"
        assert data["milestones"][0]["status"] == "draft"
        assert data["milestones"][0]["amount_dollars"] == 50.0


@pytest.mark.asyncio
class TestUpdateProject:
    async def test_update_draft_project(
        self, client: AsyncClient, freelancer_token: str, mock_stripe
    ):
        create_resp = await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Old Title",
                "client_email": "c@test.com",
                "milestones": [{"title": "M1", "amount_cents": 1000}],
            },
        )
        project_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={"title": "New Title"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"


@pytest.mark.asyncio
class TestDeleteProject:
    async def test_delete_draft_project(
        self, client: AsyncClient, freelancer_token: str, mock_stripe
    ):
        create_resp = await client.post(
            "/api/projects/",
            headers={"Authorization": f"Bearer {freelancer_token}"},
            json={
                "title": "Delete Me",
                "client_email": "c@test.com",
                "milestones": [{"title": "M1", "amount_cents": 1000}],
            },
        )
        project_id = create_resp.json()["id"]

        resp = await client.delete(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert resp.status_code == 204

        # Verify gone
        resp = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert resp.status_code == 404
