import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.auth import router as auth_router
from app.api.disputes import router as disputes_router
from app.api.health import router as health_router
from app.api.milestones import router as milestones_router
from app.api.payments import router as payments_router
from app.api.projects import router as projects_router
from app.api.ratings import router as ratings_router
from app.api.webhooks import router as webhooks_router
from app.config import settings
from app.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.utils.rate_limit import limiter

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)
logging.getLogger("stripe").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "ShieldPay starting — env=%s, frontend=%s",
        settings.environment,
        settings.frontend_url,
    )
    yield
    logger.info("ShieldPay shutting down")


def create_app() -> FastAPI:
    # Sentry error tracking
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.2 if settings.is_production else 1.0,
            send_default_pii=False,
        )

    app = FastAPI(
        title="ShieldPay API",
        description="Freelancer Payment Protection Platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware — outermost applied first
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "stripe-signature"],
        max_age=600,
    )

    # Routers
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(milestones_router)
    app.include_router(payments_router)
    app.include_router(webhooks_router)
    app.include_router(disputes_router)
    app.include_router(ratings_router)

    return app


app = create_app()
