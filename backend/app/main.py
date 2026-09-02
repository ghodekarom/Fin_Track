from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.limiter import limiter
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine
from app.db.seed import seed_categories

# Initialize logging configuration
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Automatically create all missing tables (e.g. email_verification_codes) on startup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        import logging

        logging.getLogger("uvicorn.error").warning(f"Table auto-creation notice: {exc}")

    # 2. Auto-seed default categories
    try:
        await seed_categories()
    except Exception as exc:
        import logging

        logging.getLogger("uvicorn.error").warning(f"Category auto-seeding notice: {exc}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for FinTrack Personal Expense Tracker with Authentication & Data Isolation",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Attach rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Setup CORS origins
cors_origins = []
if isinstance(settings.CORS_ORIGINS, list):
    cors_origins = [str(origin).strip().rstrip("/") for origin in settings.CORS_ORIGINS if str(origin).strip()]
else:
    cors_origins = [str(settings.CORS_ORIGINS).strip().rstrip("/")]

is_wildcard = "*" in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if not is_wildcard else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app" if not is_wildcard else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register central exception handlers
setup_exception_handlers(app)

# Mount direct health check for platforms like Render/Kubernetes
app.include_router(health_router, tags=["health"])

# Mount aggregated routes under /api
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root() -> dict:
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health",
        "api_health": "/api/health",
    }
