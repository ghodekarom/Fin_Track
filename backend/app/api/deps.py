import uuid
from typing import Annotated, Dict
from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# Re-export get_db
db_dep = Annotated[AsyncSession, Depends(get_db)]

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    db: db_dep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
) -> User:
    """Validate JWT access token and return the authenticated user."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authentication required. Please log in.")

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired access token.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token missing user subject.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user identifier in token.")

    user = await db.get(User, user_uuid)
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or account disabled.")

    return user


current_user_dep = Annotated[User, Depends(get_current_user)]


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int | None = Query(None, ge=1, description="Items per page"),
) -> Dict[str, int]:
    """Shared pagination parameter resolution dependency."""
    resolved_size = settings.DEFAULT_PAGE_SIZE
    if page_size is not None:
        resolved_size = min(page_size, settings.MAX_PAGE_SIZE)

    offset = (page - 1) * resolved_size
    return {
        "page": page,
        "page_size": resolved_size,
        "offset": offset,
    }


pagination_dep = Annotated[Dict[str, int], Depends(get_pagination_params)]
