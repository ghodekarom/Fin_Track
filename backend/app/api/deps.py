from typing import Annotated, Dict
from fastapi import Depends, Query

from app.config import settings
from app.db.session import get_db

# Re-export get_db
db_dep = Annotated[get_db, Depends()]


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
