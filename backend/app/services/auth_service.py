import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.core.security import (
    create_access_token,
    generate_random_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.email_verification import EmailVerificationCode
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
from app.services.email_service import (
    send_password_reset_email,
    send_verification_code_email,
)

logger = logging.getLogger("fintrack.auth")


async def send_registration_code(db: AsyncSession, email: str) -> None:
    """Generate and dispatch a 6-digit verification code to the target email."""
    email_clean = email.lower().strip()

    # 1. Check if user already exists
    existing = await db.execute(
        select(User).where(func.lower(User.email) == email_clean)
    )
    if existing.scalar_one_or_none():
        raise ConflictException("An account with this email already exists.")

    # 2. Invalidate previous unused codes for this email
    await db.execute(
        update(EmailVerificationCode)
        .where(
            func.lower(EmailVerificationCode.email) == email_clean,
            EmailVerificationCode.used == False,
        )
        .values(used=True)
    )

    # 3. Generate 6-digit numeric OTP and SHA-256 hash
    raw_code = f"{secrets.randbelow(1000000):06d}"
    code_hash = hash_token(raw_code)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES
    )

    record = EmailVerificationCode(
        email=email_clean,
        code_hash=code_hash,
        attempts=0,
        used=False,
        expires_at=expires_at,
    )
    db.add(record)
    await db.commit()

    # 4. Dispatch verification email
    await send_verification_code_email(email_clean, raw_code)


async def verify_and_consume_code(db: AsyncSession, email: str, raw_code: str) -> None:
    """Verify that the provided 6-digit OTP matches an active, unexpired verification record."""
    email_clean = email.lower().strip()
    query = (
        select(EmailVerificationCode)
        .where(
            func.lower(EmailVerificationCode.email) == email_clean,
            EmailVerificationCode.used == False,
        )
        .order_by(EmailVerificationCode.created_at.desc())
    )
    result = await db.execute(query)
    record = result.scalars().first()

    if not record:
        raise ValidationException(
            "Invalid or expired verification code. Please request a new code.",
            field="code",
        )

    # Check expiration
    now = datetime.now(timezone.utc)
    record_expires = (
        record.expires_at.replace(tzinfo=timezone.utc)
        if record.expires_at.tzinfo is None
        else record.expires_at
    )
    if record_expires < now:
        record.used = True
        await db.commit()
        raise ValidationException(
            "Verification code has expired. Please request a new code.",
            field="code",
        )

    # Check attempt threshold (max 5 attempts)
    if record.attempts >= 5:
        record.used = True
        await db.commit()
        raise ValidationException(
            "Too many incorrect attempts. Please request a new verification code.",
            field="code",
        )

    # Verify code hash
    expected_hash = hash_token(raw_code.strip())
    if record.code_hash != expected_hash:
        record.attempts += 1
        await db.commit()
        raise ValidationException(
            "Incorrect verification code. Please check the code and try again.",
            field="code",
        )

    # Mark code as consumed
    record.used = True
    await db.commit()


async def register_user(db: AsyncSession, schema: RegisterRequest) -> User:
    """Register a new user after successfully validating the 6-digit email OTP."""
    email_clean = schema.email.lower().strip()

    # Check if email is already taken
    existing = await db.execute(
        select(User).where(func.lower(User.email) == email_clean)
    )
    if existing.scalar_one_or_none():
        raise ConflictException("An account with this email already exists.")

    # Validate and consume the 6-digit OTP code
    await verify_and_consume_code(db, email_clean, schema.code)

    user = User(
        email=email_clean,
        full_name=schema.full_name.strip() if schema.full_name else None,
        hashed_password=hash_password(schema.password),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, schema: LoginRequest) -> User:
    """Authenticate user credentials and return active user."""
    query = select(User).where(func.lower(User.email) == schema.email.lower().strip())
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("Invalid email or password.")

    if not user.hashed_password:
        raise UnauthorizedException(
            "This account was created via Google Sign-In. Please sign in with Google or use 'Forgot Password' to set a password."
        )

    if not verify_password(schema.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password.")

    if not user.is_active:
        raise UnauthorizedException("User account is disabled.")

    return user


async def authenticate_google_user(db: AsyncSession, schema: GoogleAuthRequest) -> User:
    """Verify Google OIDC ID token, find or register user, and handle seamless account linking."""
    google_client_id = settings.GOOGLE_CLIENT_ID.strip() if settings.GOOGLE_CLIENT_ID else None
    try:
        id_info = id_token.verify_oauth2_token(
            schema.id_token,
            google_requests.Request(),
            audience=google_client_id,
            clock_skew_in_seconds=15,
        )
    except Exception as exc:
        logger.warning(f"Google token verification failed: {exc}")
        raise UnauthorizedException("Google authentication failed. Invalid or expired token.")

    google_id = id_info.get("sub")
    email = id_info.get("email")
    full_name = id_info.get("name")
    picture = id_info.get("picture")

    if not email:
        raise UnauthorizedException("Google token missing email claim.")

    email_lower = email.lower().strip()

    # 1. Search by Google ID first
    query_google = select(User).where(User.google_id == google_id)
    result_google = await db.execute(query_google)
    user = result_google.scalar_one_or_none()

    if user:
        if not user.is_active:
            raise UnauthorizedException("User account is disabled.")
        if picture and not user.avatar_url:
            user.avatar_url = picture
            await db.commit()
            await db.refresh(user)
        return user

    # 2. Search by email (Account Linking: User registered with email + password previously)
    query_email = select(User).where(func.lower(User.email) == email_lower)
    result_email = await db.execute(query_email)
    user = result_email.scalar_one_or_none()

    if user:
        if not user.is_active:
            raise UnauthorizedException("User account is disabled.")
        # Link Google ID to existing account and preserve existing password
        user.google_id = google_id
        user.is_verified = True
        if picture and not user.avatar_url:
            user.avatar_url = picture
        if full_name and not user.full_name:
            user.full_name = full_name
        await db.commit()
        await db.refresh(user)
        logger.info(f"Successfully linked Google ID to existing account for {email_lower}")
        return user

    # 3. Create brand new user via Google
    user = User(
        email=email_lower,
        full_name=full_name,
        avatar_url=picture,
        google_id=google_id,
        is_active=True,
        is_verified=True,
        hashed_password=None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"Successfully registered new user via Google Sign-In: {email_lower}")
    return user


async def create_session_tokens(
    db: AsyncSession,
    user: User,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> Tuple[str, str, int]:
    """Issue a new Access Token and cryptographically secure Refresh Token pair."""
    # 1. Short-lived Access Token (JWT)
    access_token = create_access_token(
        subject=str(user.id),
        email=user.email,
    )
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # 2. Long-lived Refresh Token (Random Hex + DB SHA-256 hash)
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
) -> Tuple[str, str, int, User]:
    """Implement Refresh Token Rotation (RTR) and Token Reuse Detection."""
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
    record_expires = (
        refresh_record.expires_at.replace(tzinfo=timezone.utc)
        if refresh_record.expires_at.tzinfo is None
        else refresh_record.expires_at
    )
    if record_expires < now:
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
    """Generate an environment-driven password reset token and dispatch email."""
    query = select(User).where(func.lower(User.email) == email.lower().strip())
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # Generic return to prevent email enumeration
    if not user or not user.is_active:
        return

    # Invalidate previous unused reset tokens for this user
    await db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used == False)
        .values(used=True)
    )

    raw_token = generate_random_token(32)
    token_hashed = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )

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
        raise ValidationException("Invalid or already used password reset link. Please request a new one.", field="token")

    now = datetime.now(timezone.utc)
    record_expires = (
        reset_record.expires_at.replace(tzinfo=timezone.utc)
        if reset_record.expires_at.tzinfo is None
        else reset_record.expires_at
    )
    if record_expires < now:
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
