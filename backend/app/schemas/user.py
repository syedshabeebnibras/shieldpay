import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_verified: bool
    stripe_account_id: str | None = None
    stripe_customer_id: str | None = None
    created_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


class OnboardingLinkResponse(BaseModel):
    url: str


class OnboardingStatusResponse(BaseModel):
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    is_verified: bool
