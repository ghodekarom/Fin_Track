from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.logging import setup_logging

# Initialize logging configuration
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for FinTrack Personal Expense Tracker (V1/MVP)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

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
    allow_credentials=not is_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register central exception handlers (centralized error shapes mapping)
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
