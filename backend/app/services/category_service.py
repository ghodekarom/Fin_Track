import uuid
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models.category import Category
from app.models.expense import Expense
from app.schemas.category import CategoryCreate, CategoryUpdate


async def get_categories(db: AsyncSession, user_id: uuid.UUID) -> list[Category]:
    """Retrieve all accessible categories (global defaults + user's custom) with user's expense count."""
    # Outer join with expenses filtered to this specific user
    query = (
        select(Category, func.count(Expense.id).label("expense_count"))
        .outerjoin(
            Expense,
            and_(Category.id == Expense.category_id, Expense.user_id == user_id),
        )
        .where(or_(Category.user_id == user_id, Category.user_id.is_(None)))
        .group_by(Category.id)
        .order_by(Category.is_default.desc(), Category.name.asc())
    )
    result = await db.execute(query)
    categories = []
    for row in result.all():
        cat, count = row
        cat.expense_count = count
        categories.append(cat)
    return categories


async def get_category_by_id(db: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    """Retrieve a category if it is accessible to the user (global or owned)."""
    query = (
        select(Category, func.count(Expense.id).label("expense_count"))
        .outerjoin(
            Expense,
            and_(Category.id == Expense.category_id, Expense.user_id == user_id),
        )
        .where(
            Category.id == category_id,
            or_(Category.user_id == user_id, Category.user_id.is_(None)),
        )
        .group_by(Category.id)
    )
    result = await db.execute(query)
    row = result.first()
    if not row:
        raise NotFoundException(f"Category with ID {category_id} not found", field="id")

    cat, count = row
    cat.expense_count = count
    return cat


async def create_category(db: AsyncSession, user_id: uuid.UUID, schema: CategoryCreate) -> Category:
    """Create a new user-owned category, ensuring name is unique among user's categories and defaults."""
    conflict_query = select(Category).where(
        or_(Category.user_id == user_id, Category.user_id.is_(None)),
        func.lower(Category.name) == schema.name.lower(),
    )
    conflict_result = await db.execute(conflict_query)
    if conflict_result.scalar_one_or_none():
        raise ConflictException(
            f"Category with name '{schema.name}' already exists", field="name"
        )

    db_category = Category(user_id=user_id, name=schema.name, is_default=False)
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    db_category.expense_count = 0
    return db_category


async def update_category(
    db: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID, schema: CategoryUpdate
) -> Category:
    """Rename an existing user-owned category."""
    category = await get_category_by_id(db, user_id, category_id)

    # Check if attempting to edit a global default category
    if category.user_id is None or category.is_default:
        raise ForbiddenException("Default system categories cannot be renamed.")

    # Check for name conflict
    conflict_query = select(Category).where(
        or_(Category.user_id == user_id, Category.user_id.is_(None)),
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
    user_id: uuid.UUID,
    category_id: uuid.UUID,
    reassign_to: uuid.UUID | None = None,
    force: bool = False,
) -> None:
    """Delete a user-owned category, applying deletion cascade/reassignment rules for this user."""
    category = await get_category_by_id(db, user_id, category_id)

    if category.user_id is None or category.is_default:
        raise ForbiddenException("Default system categories cannot be deleted.")

    # Get linked expense count for this user
    count_query = select(func.count(Expense.id)).where(
        Expense.category_id == category_id,
        Expense.user_id == user_id,
    )
    count_result = await db.execute(count_query)
    expense_count = count_result.scalar_one()

    if expense_count == 0:
        await db.delete(category)
        await db.commit()
        return

    # Category has linked expenses for this user
    if reassign_to is not None:
        target_query = select(Category).where(
            Category.id == reassign_to,
            or_(Category.user_id == user_id, Category.user_id.is_(None)),
        )
        target_result = await db.execute(target_query)
        target_category = target_result.scalar_one_or_none()
        if not target_category:
            raise NotFoundException(
                f"Reassignment target Category {reassign_to} not found",
                field="reassign_to",
            )

        # Move user's expenses to target
        await db.execute(
            update(Expense)
            .where(Expense.category_id == category_id, Expense.user_id == user_id)
            .values(category_id=reassign_to)
        )
        await db.delete(category)
        await db.commit()
        return

    if force:
        # Cascade delete linked expenses belonging to user
        await db.execute(
            delete(Expense).where(
                Expense.category_id == category_id,
                Expense.user_id == user_id,
            )
        )
        await db.delete(category)
        await db.commit()
        return

    raise ConflictException(
        message=f"Category is in use by {expense_count} expenses",
        field="id",
    )
