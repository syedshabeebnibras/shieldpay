import logging

from fastapi import APIRouter, Query, Request
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, FreelancerUser
from app.config import settings
from app.models.user import User, UserRole
from app.schemas.user import (
    AuthResponse,
    OnboardingLinkResponse,
    OnboardingStatusResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services import stripe_service
from app.utils.exceptions import BadRequestError, UnauthorizedError
from app.utils.rate_limit import AUTH_LIMIT, limiter
from app.utils.security import create_access_token, hash_password, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
@limiter.limit(AUTH_LIMIT)
async def register(request: Request, body: UserCreate, db: DbSession) -> AuthResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none() is not None:
        raise BadRequestError("Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )

    # Stripe account creation is optional — don't block signup if it fails
    if body.role == UserRole.FREELANCER:
        try:
            user.stripe_account_id = await stripe_service.create_connect_account(body.email)
        except Exception:
            logger.warning("Stripe Connect account creation failed for %s — user can set up later", body.email)

    if body.role == UserRole.CLIENT:
        try:
            user.stripe_customer_id = await stripe_service.create_customer(body.email)
        except Exception:
            logger.warning("Stripe Customer creation failed for %s — user can set up later", body.email)

    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=token,
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit(AUTH_LIMIT)
async def login(request: Request, body: UserLogin, db: DbSession) -> AuthResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")

    token = create_access_token(data={"sub": str(user.id)})

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=token,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/stripe/onboarding-link", response_model=OnboardingLinkResponse)
async def create_onboarding_link(
    current_user: FreelancerUser,
) -> OnboardingLinkResponse:
    if not current_user.stripe_account_id:
        raise BadRequestError("No Stripe Connect account found. Please contact support.")

    return_url = f"{settings.frontend_url}/dashboard/settings?stripe_onboarding=complete"
    refresh_url = f"{settings.frontend_url}/dashboard/settings?stripe_onboarding=refresh"

    url = await stripe_service.create_account_link(
        account_id=current_user.stripe_account_id,
        return_url=return_url,
        refresh_url=refresh_url,
    )

    return OnboardingLinkResponse(url=url)


@router.get("/stripe/onboarding-callback", response_model=OnboardingStatusResponse)
async def onboarding_callback(
    current_user: FreelancerUser,
    db: DbSession,
    account_id: str = Query(...),
) -> OnboardingStatusResponse:
    if current_user.stripe_account_id != account_id:
        raise BadRequestError("Account ID mismatch")

    status = await stripe_service.get_account_status(account_id)

    is_verified = status["charges_enabled"] and status["payouts_enabled"]
    if is_verified and not current_user.is_verified:
        current_user.is_verified = True
        await db.flush()

    return OnboardingStatusResponse(
        charges_enabled=status["charges_enabled"],
        payouts_enabled=status["payouts_enabled"],
        details_submitted=status["details_submitted"],
        is_verified=is_verified,
    )
