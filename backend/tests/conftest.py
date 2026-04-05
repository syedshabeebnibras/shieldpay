import os

os.environ["RATE_LIMIT_ENABLED"] = "false"

from unittest.mock import AsyncMock, patch

import pytest
import stripe
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import get_db
from app.main import app

TABLE_NAMES = [
    "webhook_events", "ratings", "disputes", "payments", "milestones", "projects", "users"
]


@pytest.fixture
async def db_engine():
    """Create a fresh engine per test to avoid event loop issues."""
    engine = create_async_engine(settings.database_url, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(autouse=True)
async def _clean_data(db_engine):
    """Delete all data before each test."""
    async with db_engine.begin() as conn:
        for name in TABLE_NAMES:
            await conn.execute(text(f"DELETE FROM {name}"))
    yield


@pytest.fixture
async def client(db_engine):
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def mock_stripe():
    with (
        patch(
            "app.api.auth.stripe_service.create_connect_account",
            new_callable=AsyncMock,
            return_value="acct_test_123",
        ) as mock_connect,
        patch(
            "app.api.auth.stripe_service.create_customer",
            new_callable=AsyncMock,
            return_value="cus_test_456",
        ) as mock_customer,
        patch(
            "app.api.auth.stripe_service.create_account_link",
            new_callable=AsyncMock,
            return_value="https://connect.stripe.com/setup/test",
        ) as mock_link,
        patch(
            "app.api.auth.stripe_service.get_account_status",
            new_callable=AsyncMock,
            return_value={
                "charges_enabled": True,
                "payouts_enabled": True,
                "details_submitted": True,
            },
        ) as mock_status,
    ):
        yield {
            "create_connect_account": mock_connect,
            "create_customer": mock_customer,
            "create_account_link": mock_link,
            "get_account_status": mock_status,
        }


@pytest.fixture
async def freelancer_token(client: AsyncClient, mock_stripe) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "freelancer@test.com",
            "password": "testpass123",
            "full_name": "Test Freelancer",
            "role": "freelancer",
        },
    )
    return resp.json()["access_token"]


@pytest.fixture
async def client_token(client: AsyncClient, mock_stripe) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "client@test.com",
            "password": "testpass123",
            "full_name": "Test Client",
            "role": "client",
        },
    )
    return resp.json()["access_token"]


@pytest.fixture
def bypass_stripe_sig():
    """Patch construct_event to return a crafted event dict."""

    def _make_patcher(event: dict):
        return patch(
            "stripe.Webhook.construct_event",
            return_value=event,
        )

    return _make_patcher
