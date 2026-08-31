import uuid
from datetime import datetime, timedelta, timezone
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ConflictException, NotFoundException, UnauthorizedException, ValidationException
from app.core.security import (
    create_access_token,
    generate_random_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.password_reset import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.services.email_service import send_password_reset_email


async def register_user(db: AsyncSession, schema: RegisterRequest) -> User:
    """Register a new user with email and password."""
    # Check for existing email (case-insensitive)
    existing_query = select(User).where(func.lower(User.email) == schema.email.lower())
    result = await db.execute(existing_query)
    if result.scalar_one_or_none():
        raise ConflictException("A user with this email address already exists.", field="email")

    user = User(
        email=schema.email.lower().strip(),
        hashed_password=hash_password(schema.password),
        full_name=schema.full_name.strip() if schema.full_name else None,
        is_verified=False,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, schema: LoginRequest) -> User:
    """Authenticate a user using email and password."""
    query = select(User).where(func.lower(User.email) == schema.email.lower())
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise UnauthorizedException("Invalid email or password.")

    if not verify_password(schema.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password.")

    if not user.is_active:
        raise UnauthorizedException("Account has been disabled.")

    return user


async def authenticate_google_user(db: AsyncSession, schema: GoogleAuthRequest) -> User:
    """Verify Google OIDC ID token and authenticate or register/link the user."""
    try:
        request = google_requests.Request()
        # Verify token with Google public certs
        id_info = google_id_token.verify_oauth2_token(
            schema.id_token,
            request,
            settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else None,
        )
    except Exception as exc:
        raise UnauthorizedException(f"Invalid Google authentication token: {exc}")

    google_sub = id_info.get("sub")
    email = id_info.get("email")
    name = id_info.get("name")
    picture = id_info.get("picture")

    if not email or not google_sub:
        raise UnauthorizedException("Google authentication token did not contain valid email or user identity.")

    email_lower = email.lower().strip()

    # 1. Check if user with google_id exists
    query = select(User).where(User.google_id == google_sub)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user:
        if not user.is_active:
            raise UnauthorizedException("Account has been disabled.")
        # Update avatar or name if updated on Google
        if picture and user.avatar_url != picture:
            user.avatar_url = picture
            await db.commit()
        return user

    # 2. Check if user with matching email already exists (Account Linking)
    query_email = select(User).where(func.lower(User.email) == email_lower)
    result_email = await db.execute(query_email)
    user_by_email = result_email.scalar_one_or_none()

    if user_by_email:
        if not user_by_email.is_active:
            raise UnauthorizedException("Account has been disabled.")
        user_by_email.google_id = google_sub
        user_by_email.is_verified = True
        if picture and not user_by_email.avatar_url:
            user_by_email.avatar_url = picture
        if name and not user_by_email.full_name:
            user_by_email.full_name = name
        await db.commit()
        await db.refresh(user_by_email)
        return user_by_email

    # 3. Create new user via Google Sign-In
    new_user = User(
        email=email_lower,
        google_id=google_sub,
        full_name=name,
        avatar_url=picture,
        hashed_password=None,
        is_verified=True,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def create_session_tokens(
    db: AsyncSession,
    user: User,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, str, int]:
    """
    Create an access token and a refresh token.
    Returns: (access_token, raw_refresh_token, expires_in_seconds)
    """
    # 1. Generate Access Token
    access_token = create_access_token(
        subject=str(user.id),
        email=user.email,
    )
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # 2. Generate and store Refresh Token
    raw_refresh_token = generate_random_token(64)
    token_hashed = hash_token(raw_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_refresh = RefreshToken(
        token_hash=token_hashed,
        user_id=user.id,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(db_refresh)
    await db.commit()

    return access_token, raw_refresh_token, expires_in


async def rotate_refresh_token(
    db: AsyncSession,
    raw_refresh_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, str, int, User]:
    """
    Rotate a refresh token using Refresh Token Rotation (RTR).
    If a revoked token is reused, all user refresh tokens are immediately revoked.
    """
    token_hashed = hash_token(raw_refresh_token)

    query = select(RefreshToken).where(RefreshToken.token_hash == token_hashed)
    result = await db.execute(query)
    refresh_record = result.scalar_one_or_none()

    if not refresh_record:
        raise UnauthorizedException("Invalid refresh token.")

    # Fetch associated user
    user = await db.get(User, refresh_record.user_id)
    if not user or not user.is_active:
        raise UnauthorizedException("User account not found or disabled.")

    # Reuse Detection: If token is already revoked, compromise detected!
    if refresh_record.revoked:
        await revoke_all_user_tokens(db, user.id)
        raise UnauthorizedException("Compromised session detected. All sessions have been logged out.")

    # Check expiration
    now = datetime.now(timezone.utc)
    if refresh_record.expires_at < now:
        refresh_record.revoked = True
        await db.commit()
        raise UnauthorizedException("Refresh token has expired.")

    # Invalidate old refresh token
    refresh_record.revoked = True

    # Generate new token pair
    new_access_token = create_access_token(
        subject=str(user.id),
        email=user.email,
    )
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    new_raw_refresh_token = generate_random_token(64)
    new_token_hashed = hash_token(new_raw_refresh_token)
    new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_db_refresh = RefreshToken(
        token_hash=new_token_hashed,
        user_id=user.id,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=new_expires_at,
        revoked=False,
    )
    db.add(new_db_refresh)
    await db.commit()

    return new_access_token, new_raw_refresh_token, expires_in, user


async def revoke_token(db: AsyncSession, raw_refresh_token: str) -> None:
    """Revoke a specific refresh token session on logout."""
    token_hashed = hash_token(raw_refresh_token)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hashed)
        .values(revoked=True)
    )
    await db.commit()


async def revoke_all_user_tokens(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Revoke all active refresh tokens for a user (logout all devices)."""
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
        .values(revoked=True)
    )
    await db.commit()


async def request_password_reset(db: AsyncSession, email: str) -> None:
    """Generate a password reset token and dispatch email."""
    query = select(User).where(func.lower(User.email) == email.lower().strip())
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # Generic return to prevent email enumeration
    if not user or not user.is_active:
        return

    raw_token = generate_random_token(32)
    token_hashed = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    reset_record = PasswordResetToken(
        token_hash=token_hashed,
        user_id=user.id,
        expires_at=expires_at,
        used=False,
    )
    db.add(reset_record)
    await db.commit()

    # Send reset email
    await send_password_reset_email(user.email, raw_token)


async def reset_password(db: AsyncSession, schema: ResetPasswordRequest) -> None:
    """Reset a user's password using a valid reset token."""
    token_hashed = hash_token(schema.token)

    query = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hashed)
    result = await db.execute(query)
    reset_record = result.scalar_one_or_none()

    if not reset_record or reset_record.used:
        raise ValidationException("Invalid or expired password reset link.", field="token")

    now = datetime.now(timezone.utc)
    if reset_record.expires_at < now:
        raise ValidationException("Password reset link has expired. Please request a new one.", field="token")

    user = await db.get(User, reset_record.user_id)
    if not user or not user.is_active:
        raise NotFoundException("User account not found or disabled.")

    # Update password
    user.hashed_password = hash_password(schema.new_password)
    user.is_verified = True
    reset_record.used = True

    # Revoke all existing sessions for security
    await revoke_all_user_tokens(db, user.id)
    await db.commit()


async def change_user_password(db: AsyncSession, user_id: uuid.UUID, schema: ChangePasswordRequest) -> None:
    """Change an authenticated user's password."""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException("User not found.")

    if user.hashed_password and not verify_password(schema.current_password, user.hashed_password):
        raise UnauthorizedException("Current password is incorrect.", field="current_password")

    user.hashed_password = hash_password(schema.new_password)
    await db.commit()
