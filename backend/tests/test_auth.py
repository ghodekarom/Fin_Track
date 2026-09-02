from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.models.email_verification import EmailVerificationCode
from app.models.refresh_token import RefreshToken
from app.models.user import User


@pytest.mark.asyncio
async def test_send_verification_code_success(client: AsyncClient, db_session: AsyncSession):
    """Test dispatching a 6-digit OTP code to an email address."""
    response = await client.post(
        "/api/auth/send-verification-code",
        json={"email": "newuser@example.com"},
    )
    assert response.status_code == 200
    assert "Verification code sent" in response.json()["message"]

    # Verify record was stored with SHA-256 hash
    query = select(EmailVerificationCode).where(
        EmailVerificationCode.email == "newuser@example.com"
    )
    result = await db_session.execute(query)
    record = result.scalars().first()
    assert record is not None
    assert record.used is False
    assert record.attempts == 0
    assert len(record.code_hash) == 64  # SHA-256 hex length


@pytest.mark.asyncio
async def test_send_verification_code_duplicate_email_fails(client: AsyncClient, test_user: User):
    """Test requesting verification code for already registered email returns 409 Conflict."""
    response = await client.post(
        "/api/auth/send-verification-code",
        json={"email": test_user.email},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_register_user_with_otp_flow(client: AsyncClient, db_session: AsyncSession):
    """Test the full email verification + registration cycle."""
    email = "signup@example.com"

    # 1. Send verification code
    send_res = await client.post(
        "/api/auth/send-verification-code",
        json={"email": email},
    )
    assert send_res.status_code == 200

    # Retrieve record from DB and set a known code
    query = select(EmailVerificationCode).where(
        EmailVerificationCode.email == email,
        EmailVerificationCode.used == False,
    )
    result = await db_session.execute(query)
    record = result.scalars().first()
    assert record is not None

    test_otp = "849201"
    record.code_hash = hash_token(test_otp)
    await db_session.commit()

    # 2. Try registering with wrong code -> fails
    bad_res = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "code": "000000",
            "full_name": "Verified User",
        },
    )
    assert bad_res.status_code in (400, 422)

    # 3. Register with correct OTP code -> 201 Created
    good_res = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "code": test_otp,
            "full_name": "Verified User",
        },
    )
    assert good_res.status_code == 201
    data = good_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == email
    assert data["user"]["full_name"] == "Verified User"
    assert data["user"]["is_verified"] is True
    assert "fintrack_refresh_token" in good_res.cookies

    # 4. Reusing consumed code fails
    replay_res = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "code": test_otp,
            "full_name": "Verified User",
        },
    )
    assert replay_res.status_code in (400, 409, 422)


@pytest.mark.asyncio
async def test_register_expired_code_fails(client: AsyncClient, db_session: AsyncSession):
    """Test registering with an expired OTP code fails."""
    email = "expired@example.com"
    test_otp = "654321"

    # Create expired record
    expired_record = EmailVerificationCode(
        email=email,
        code_hash=hash_token(test_otp),
        attempts=0,
        used=False,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    db_session.add(expired_record)
    await db_session.commit()

    res = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "code": test_otp,
            "full_name": "Expired Code User",
        },
    )
    assert res.status_code in (400, 422)


@pytest.mark.asyncio
async def test_login_success_and_invalid_password(client: AsyncClient, test_user: User):
    """Test login with valid credentials vs invalid credentials."""
    # 1. Invalid password
    bad_login = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 2. Valid password
    good_login = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert good_login.status_code == 200
    data = good_login.json()
    assert "access_token" in data
    assert data["user"]["email"] == test_user.email
    assert "fintrack_refresh_token" in good_login.cookies


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, test_user: User, auth_headers: dict[str, str]):
    """Test retrieving authenticated user profile."""
    # Without token -> 401
    res_unauth = await client.get("/api/auth/me")
    assert res_unauth.status_code == 401

    # With token -> 200
    res_auth = await client.get("/api/auth/me", headers=auth_headers)
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert data["email"] == test_user.email
    assert data["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient, test_user: User, db_session: AsyncSession):
    """Test refresh token rotation issues new access and refresh tokens and revokes the old one."""
    # 1. Login to get refresh token
    login_res = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert login_res.status_code == 200
    old_refresh_cookie = login_res.cookies.get("fintrack_refresh_token")
    assert old_refresh_cookie is not None

    # 2. Call /refresh with cookie
    client.cookies.set("fintrack_refresh_token", old_refresh_cookie)
    refresh_res = await client.post("/api/auth/refresh")
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data

    new_refresh_cookie = refresh_res.cookies.get("fintrack_refresh_token")
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != old_refresh_cookie

    # 3. Verify old refresh token is marked revoked in DB
    old_hash = hash_token(old_refresh_cookie)
    query = select(RefreshToken).where(RefreshToken.token_hash == old_hash)
    result = await db_session.execute(query)
    old_record = result.scalar_one()
    assert old_record.revoked is True


@pytest.mark.asyncio
async def test_reuse_detection_revokes_all_sessions(client: AsyncClient, test_user: User, db_session: AsyncSession):
    """Test that reusing a revoked refresh token revokes all user sessions."""
    # 1. Login
    login_res = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    old_refresh = login_res.cookies.get("fintrack_refresh_token")

    # 2. Rotate once
    client.cookies.set("fintrack_refresh_token", old_refresh)
    rotate_res = await client.post("/api/auth/refresh")
    assert rotate_res.status_code == 200
    new_refresh = rotate_res.cookies.get("fintrack_refresh_token")

    # 3. Attempt to use OLD (revoked) refresh token -> triggers reuse detection!
    client.cookies.set("fintrack_refresh_token", old_refresh)
    compromised_res = await client.post("/api/auth/refresh")
    assert compromised_res.status_code == 401
    assert "Compromised" in compromised_res.json()["error"]["message"]

    # 4. Verify NEW refresh token was also revoked due to reuse detection
    new_hash = hash_token(new_refresh)
    query = select(RefreshToken).where(RefreshToken.token_hash == new_hash)
    result = await db_session.execute(query)
    new_record = result.scalar_one()
    assert new_record.revoked is True


@pytest.mark.asyncio
async def test_logout_and_logout_all(client: AsyncClient, test_user: User, auth_headers: dict[str, str], db_session: AsyncSession):
    """Test single logout and logout-all endpoints."""
    # 1. Login
    login_res = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    refresh_token = login_res.cookies.get("fintrack_refresh_token")
    client.cookies.set("fintrack_refresh_token", refresh_token)

    # 2. Single logout
    logout_res = await client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    # Verify token revoked in DB
    query = select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    result = await db_session.execute(query)
    assert result.scalar_one().revoked is True

    # 3. Logout all
    logout_all_res = await client.post("/api/auth/logout-all", headers=auth_headers)
    assert logout_all_res.status_code == 200
