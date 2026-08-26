from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import db_dep

router = APIRouter()


@router.get("/health")
async def health_check(db: db_dep) -> dict:
    """Check connectivity to PostgreSQL database and application status."""
    try:
        # Perform query to verify DB connection is active
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "db": db_status,
        "version": "1.0.0",
    }
