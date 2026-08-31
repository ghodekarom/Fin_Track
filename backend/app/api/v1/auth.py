from fastapi import APIRouter, Cookie, Header, Request, Response, status
from typing import Annotated

from app.api.deps import current_user_dep, db_dep
from app.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter()

REFRESH_COOKIE_NAME = "fintrack_refresh_token"


def set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    """Set secure HttpOnly refresh token cookie on the response."""
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    is_prod = settings.APP_ENV == "production"
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        max_age=max_age,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        path="/api/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie."""
    is_prod = settings.APP_ENV == "production"
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        path="/api/auth",
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def register(
    request: Request,
    response: Response,
    db: db_dep,
    payload: RegisterRequest,
    user_agent: Annotated[str | None, Header()] = None,
) -> TokenResponse:
    """Register a new user account with email and password."""
    user = await auth_service.register_user(db, payload)
    client_ip = request.client.host if request.client else None
    access_token, raw_refresh, expires_in = await auth_service.create_session_tokens(
        db, user, user_agent=user_agent, ip_address=client_ip
    )
    set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(
    request: Request,
    response: Response,
    db: db_dep,
    payload: LoginRequest,
    user_agent: Annotated[str | None, Header()] = None,
) -> TokenResponse:
    """Authenticate user with email and password."""
    user = await auth_service.authenticate_user(db, payload)
    client_ip = request.client.host if request.client else None
    access_token, raw_refresh, expires_in = await auth_service.create_session_tokens(
        db, user, user_agent=user_agent, ip_address=client_ip
    )
    set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post("/google", response_model=TokenResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def google_auth(
    request: Request,
    response: Response,
    db: db_dep,
    payload: GoogleAuthRequest,
    user_agent: Annotated[str | None, Header()] = None,
) -> TokenResponse:
    """Authenticate or register user via Google OIDC ID token."""
    user = await auth_service.authenticate_google_user(db, payload)
    client_ip = request.client.host if request.client else None
    access_token, raw_refresh, expires_in = await auth_service.create_session_tokens(
        db, user, user_agent=user_agent, ip_address=client_ip
    )
    set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: db_dep,
    user_agent: Annotated[str | None, Header()] = None,
) -> RefreshTokenResponse:
    """Rotate refresh token and issue new access token via HttpOnly cookie."""
    cookie_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not cookie_token:
        raise UnauthorizedException("Refresh token cookie not provided.")

    client_ip = request.client.host if request.client else None
    new_access, new_refresh, expires_in, _ = await auth_service.rotate_refresh_token(
        db, cookie_token, user_agent=user_agent, ip_address=client_ip
    )
    set_refresh_cookie(response, new_refresh)
    return RefreshTokenResponse(
        access_token=new_access,
        expires_in=expires_in,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    db: db_dep,
) -> MessageResponse:
    """Revoke active refresh token and clear cookie."""
    cookie_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if cookie_token:
        await auth_service.revoke_token(db, cookie_token)
    clear_refresh_cookie(response)
    return MessageResponse(message="Successfully logged out.")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    response: Response,
    db: db_dep,
    current_user: current_user_dep,
) -> MessageResponse:
    """Revoke all active sessions on all devices for the current user."""
    await auth_service.revoke_all_user_tokens(db, current_user.id)
    clear_refresh_cookie(response)
    return MessageResponse(message="Successfully logged out of all devices.")


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit(settings.PASSWORD_RESET_RATE_LIMIT)
async def forgot_password(
    request: Request,
    db: db_dep,
    payload: ForgotPasswordRequest,
) -> MessageResponse:
    """Request a password reset link to be sent to user's email."""
    await auth_service.request_password_reset(db, payload.email)
    return MessageResponse(
        message="If your email is registered, you will receive a password reset link shortly."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    db: db_dep,
    payload: ResetPasswordRequest,
) -> MessageResponse:
    """Reset password using token received from email."""
    await auth_service.reset_password(db, payload)
    return MessageResponse(message="Your password has been successfully reset. Please log in.")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    db: db_dep,
    current_user: current_user_dep,
    payload: ChangePasswordRequest,
) -> MessageResponse:
    """Change password for the authenticated user."""
    await auth_service.change_user_password(db, current_user.id, payload)
    return MessageResponse(message="Your password has been updated successfully.")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: current_user_dep,
) -> UserResponse:
    """Get profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)
