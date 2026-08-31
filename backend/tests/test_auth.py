import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.models.refresh_token import RefreshToken
from app.models.user import User


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Test user registration creates user and sets refresh cookie."""
    payload = {
        "email": "newuser@example.com",
        "password": "SecurePassword123!",
        "full_name": "New User",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["full_name"] == "New User"
    assert "fintrack_refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client: AsyncClient, test_user: User):
    """Test registering with an existing email returns 409 Conflict."""
    payload = {
        "email": test_user.email,
        "password": "AnotherPassword123!",
        "full_name": "Duplicate User",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


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
