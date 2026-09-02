import asyncio
import uuid
from typing import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import pool

from app.config import settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base, User
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create session-scoped asyncio event loop for testing."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Initialize test database engine and schema."""
    engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_database(test_engine):
    """Automatically clean database tables before each test to ensure isolation."""
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for test setup/assertions."""
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """Provide an unauthenticated HTTP client configured with db session overrides."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async_session = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a primary test user."""
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Primary Test User",
        is_verified=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Generate authorization Bearer header for test_user."""
    token = create_access_token(subject=str(test_user.id), email=test_user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_client(client: AsyncClient, auth_headers: dict[str, str]) -> AsyncClient:
    """Provide an HTTP client authenticated as test_user."""
    client.headers.update(auth_headers)
    return client


@pytest.fixture
async def second_user(db_session: AsyncSession) -> User:
    """Create a secondary test user for cross-user data isolation tests."""
    user = User(
        id=uuid.uuid4(),
        email="seconduser@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Secondary Test User",
        is_verified=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def second_auth_headers(second_user: User) -> dict[str, str]:
    """Generate authorization Bearer header for second_user."""
    token = create_access_token(subject=str(second_user.id), email=second_user.email)
    return {"Authorization": f"Bearer {token}"}
