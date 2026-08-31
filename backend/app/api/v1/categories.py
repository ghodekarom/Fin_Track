import uuid
from fastapi import APIRouter, Query, status

from app.api.deps import current_user_dep, db_dep
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import category_service

router = APIRouter()


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    db: db_dep,
    current_user: current_user_dep,
) -> list[CategoryResponse]:
    """List all categories (defaults + user-created) with user-specific linked expense counts."""
    return await category_service.get_categories(db, current_user.id)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    db: db_dep,
    current_user: current_user_dep,
    payload: CategoryCreate,
) -> CategoryResponse:
    """Create a new user-scoped category."""
    return await category_service.create_category(db, current_user.id, payload)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    db: db_dep,
    current_user: current_user_dep,
    category_id: uuid.UUID,
) -> CategoryResponse:
    """Get detail of a single category accessible to the user."""
    return await category_service.get_category_by_id(db, current_user.id, category_id)


@router.put("/{category_id}", response_model=CategoryResponse)
async def rename_category(
    db: db_dep,
    current_user: current_user_dep,
    category_id: uuid.UUID,
    payload: CategoryUpdate,
) -> CategoryResponse:
    """Rename an existing user-owned category."""
    return await category_service.update_category(db, current_user.id, category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    db: db_dep,
    current_user: current_user_dep,
    category_id: uuid.UUID,
    reassign_to: uuid.UUID | None = Query(
        None, description="Reassign expenses to this category ID before deleting"
    ),
    force: bool = Query(
        False, description="Cascade delete all linked expenses under this category"
    ),
) -> None:
    """Delete a user-owned category. Supports cascading or reassigning of linked expenses."""
    await category_service.delete_category(db, current_user.id, category_id, reassign_to, force)
