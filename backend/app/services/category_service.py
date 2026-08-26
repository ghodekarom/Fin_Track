import uuid
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.category import Category
from app.models.expense import Expense
from app.schemas.category import CategoryCreate, CategoryUpdate


async def get_categories(db: AsyncSession) -> list[Category]:
    """Retrieve all categories with the count of linked expenses."""
    query = (
        select(Category, func.count(Expense.id).label("expense_count"))
        .outerjoin(Expense, Category.id == Expense.category_id)
        .group_by(Category.id)
        .order_by(Category.name)
    )
    result = await db.execute(query)
    categories = []
    for row in result.all():
        cat, count = row
        cat.expense_count = count
        categories.append(cat)
    return categories


async def get_category_by_id(db: AsyncSession, category_id: uuid.UUID) -> Category:
    """Retrieve a single category by ID, raising NotFoundException if missing."""
    # Count linked expenses too for single read compatibility
    query = (
        select(Category, func.count(Expense.id).label("expense_count"))
        .outerjoin(Expense, Category.id == Expense.category_id)
        .where(Category.id == category_id)
        .group_by(Category.id)
    )
    result = await db.execute(query)
    row = result.first()
    if not row:
        raise NotFoundException(f"Category with ID {category_id} not found", field="id")

    cat, count = row
    cat.expense_count = count
    return cat


async def create_category(db: AsyncSession, schema: CategoryCreate) -> Category:
    """Create a new category, ensuring name is case-insensitively unique."""
    # Check for name conflict
    conflict_query = select(Category).where(
        func.lower(Category.name) == schema.name.lower()
    )
    conflict_result = await db.execute(conflict_query)
    if conflict_result.scalar_one_or_none():
        raise ConflictException(
            f"Category with name '{schema.name}' already exists", field="name"
        )

    db_category = Category(name=schema.name, is_default=False)
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    db_category.expense_count = 0
    return db_category


async def update_category(
    db: AsyncSession, category_id: uuid.UUID, schema: CategoryUpdate
) -> Category:
    """Rename an existing category."""
    category = await get_category_by_id(db, category_id)

    # Check for name conflict with other categories
    conflict_query = select(Category).where(
        func.lower(Category.name) == schema.name.lower(),
        Category.id != category_id,
    )
    conflict_result = await db.execute(conflict_query)
    if conflict_result.scalar_one_or_none():
        raise ConflictException(
            f"Category with name '{schema.name}' already exists", field="name"
        )

    category.name = schema.name
    await db.commit()
    await db.refresh(category)
    return category


async def delete_category(
    db: AsyncSession,
    category_id: uuid.UUID,
    reassign_to: uuid.UUID | None = None,
    force: bool = False,
) -> None:
    """Delete a category, applying the deletion cascade/conflict rules."""
    category = await get_category_by_id(db, category_id)

    # Get linked expense count
    count_query = select(func.count(Expense.id)).where(
        Expense.category_id == category_id
    )
    count_result = await db.execute(count_query)
    expense_count = count_result.scalar_one()

    if expense_count == 0:
        # Category is safe to delete directly
        await db.delete(category)
        await db.commit()
        return

    # Category has linked expenses
    if reassign_to is not None:
        # Verify target category exists
        target_category = await db.get(Category, reassign_to)
        if not target_category:
            raise NotFoundException(
                f"Reassignment target Category {reassign_to} not found",
                field="reassign_to",
            )

        # Move expenses to target
        await db.execute(
            update(Expense)
            .where(Expense.category_id == category_id)
            .values(category_id=reassign_to)
        )
        await db.delete(category)
        await db.commit()
        return

    if force:
        # Cascade delete linked expenses first
        await db.execute(delete(Expense).where(Expense.category_id == category_id))
        await db.delete(category)
        await db.commit()
        return

    # Otherwise, raise a ConflictException with count details
    raise ConflictException(
        message=f"Category is in use by {expense_count} expenses",
        field="id",
    )
