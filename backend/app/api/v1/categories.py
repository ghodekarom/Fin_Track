import uuid
from fastapi import APIRouter, Query, status

from app.api.deps import db_dep
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import category_service

router = APIRouter()


@router.get("", response_model=list[CategoryResponse])
async def list_categories(db: db_dep) -> list[CategoryResponse]:
    """List all categories with their linked expense counts."""
    return await category_service.get_categories(db)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(db: db_dep, payload: CategoryCreate) -> CategoryResponse:
    """Create a new category by name."""
    return await category_service.create_category(db, payload)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(db: db_dep, category_id: uuid.UUID) -> CategoryResponse:
    """Get detail of a single category."""
    return await category_service.get_category_by_id(db, category_id)


@router.put("/{category_id}", response_model=CategoryResponse)
async def rename_category(
    db: db_dep, category_id: uuid.UUID, payload: CategoryUpdate
) -> CategoryResponse:
    """Rename an existing category."""
    return await category_service.update_category(db, category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    db: db_dep,
    category_id: uuid.UUID,
    reassign_to: uuid.UUID | None = Query(
        None, description="Reassign expenses to this category ID before deleting"
    ),
    force: bool = Query(
        False, description="Cascade delete all linked expenses under this category"
    ),
) -> None:
    """Delete a category. Supports cascading or reassigning of linked expenses."""
    await category_service.delete_category(db, category_id, reassign_to, force)
DarkTheme = True
