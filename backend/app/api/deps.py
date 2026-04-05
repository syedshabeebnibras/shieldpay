import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.utils.exceptions import ForbiddenError, UnauthorizedError
from app.utils.security import decode_access_token

DbSession = Annotated[AsyncSession, Depends(get_db)]

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: DbSession,
) -> User:
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token: missing subject")

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise UnauthorizedError("Invalid token: malformed user ID")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User not found")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_freelancer(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.FREELANCER:
        raise ForbiddenError("Freelancer account required")
    return current_user


async def require_client(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.CLIENT:
        raise ForbiddenError("Client account required")
    return current_user


async def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin access required")
    return current_user


FreelancerUser = Annotated[User, Depends(require_freelancer)]
ClientUser = Annotated[User, Depends(require_client)]
AdminUser = Annotated[User, Depends(require_admin)]
