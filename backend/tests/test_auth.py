import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegister:
    async def test_register_freelancer(self, client: AsyncClient, mock_stripe):
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "alice@example.com",
                "password": "securepass1",
                "full_name": "Alice Smith",
                "role": "freelancer",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["access_token"]
        assert data["user"]["email"] == "alice@example.com"
        assert data["user"]["role"] == "freelancer"
        assert data["user"]["stripe_account_id"] == "acct_test_123"
        mock_stripe["create_connect_account"].assert_called_once_with(
            "alice@example.com"
        )

    async def test_register_client(self, client: AsyncClient, mock_stripe):
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "bob@example.com",
                "password": "securepass1",
                "full_name": "Bob Jones",
                "role": "client",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["user"]["role"] == "client"
        assert data["user"]["stripe_customer_id"] == "cus_test_456"
        mock_stripe["create_customer"].assert_called_once_with("bob@example.com")

    async def test_register_duplicate_email(self, client: AsyncClient, mock_stripe):
        body = {
            "email": "dupe@example.com",
            "password": "securepass1",
            "full_name": "Dupe User",
            "role": "freelancer",
        }
        resp1 = await client.post("/api/auth/register", json=body)
        assert resp1.status_code == 201

        resp2 = await client.post("/api/auth/register", json=body)
        assert resp2.status_code == 400
        assert "already registered" in resp2.json()["detail"].lower()

    async def test_register_short_password(self, client: AsyncClient, mock_stripe):
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "short@example.com",
                "password": "short",
                "full_name": "Short Pass",
                "role": "client",
            },
        )
        assert resp.status_code == 422  # Pydantic validation

    async def test_register_invalid_email(self, client: AsyncClient, mock_stripe):
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepass1",
                "full_name": "Bad Email",
                "role": "client",
            },
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient, mock_stripe):
        await client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "securepass1",
                "full_name": "Login User",
                "role": "freelancer",
            },
        )

        resp = await client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "securepass1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["user"]["email"] == "login@example.com"

    async def test_login_wrong_password(self, client: AsyncClient, mock_stripe):
        await client.post(
            "/api/auth/register",
            json={
                "email": "wrong@example.com",
                "password": "securepass1",
                "full_name": "Wrong Pass",
                "role": "client",
            },
        )

        resp = await client.post(
            "/api/auth/login",
            json={"email": "wrong@example.com", "password": "badpassword1"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/api/auth/login",
            json={"email": "ghost@example.com", "password": "securepass1"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestMe:
    async def test_get_me(self, client: AsyncClient, freelancer_token: str):
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "freelancer@test.com"

    async def test_get_me_no_token(self, client: AsyncClient):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 403  # HTTPBearer returns 403 when no creds

    async def test_get_me_bad_token(self, client: AsyncClient):
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestStripeOnboarding:
    async def test_onboarding_link(self, client: AsyncClient, freelancer_token: str, mock_stripe):
        resp = await client.post(
            "/api/auth/stripe/onboarding-link",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["url"] == "https://connect.stripe.com/setup/test"

    async def test_onboarding_link_client_forbidden(
        self, client: AsyncClient, client_token: str, mock_stripe
    ):
        resp = await client.post(
            "/api/auth/stripe/onboarding-link",
            headers={"Authorization": f"Bearer {client_token}"},
        )
        assert resp.status_code == 403

    async def test_onboarding_callback(self, client: AsyncClient, freelancer_token: str, mock_stripe):
        # First get the user to find their account ID
        me_resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        account_id = me_resp.json()["stripe_account_id"]

        resp = await client.get(
            f"/api/auth/stripe/onboarding-callback?account_id={account_id}",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["charges_enabled"] is True
        assert data["is_verified"] is True

        # Verify user is now marked as verified
        me_resp2 = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {freelancer_token}"},
        )
        assert me_resp2.json()["is_verified"] is True
