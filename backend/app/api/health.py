from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Health check that doesn't depend on the DB session dependency."""
    db_ok = False
    try:
        engine = create_async_engine(settings.database_url, pool_size=1)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_ok = True
        await engine.dispose()
    except Exception:
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "environment": settings.environment,
        "database": "connected" if db_ok else "unreachable",
    }
