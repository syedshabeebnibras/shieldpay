from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: DbSession) -> dict:
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "environment": settings.environment,
        "database": "connected" if db_ok else "unreachable",
    }
