import math
import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.category import Category
from app.models.expense import Expense
from app.models.budget import Budget
from app.services.budget_service import get_month_range
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


async def get_expenses(
    db: AsyncSession, filters: dict, pagination: dict
) -> dict:
    """Retrieve filtered, sorted, and paginated expenses."""
    query = (
        select(Expense)
        .options(joinedload(Expense.category))
        .join(Category, Expense.category_id == Category.id)
    )

    # Search (title, notes)
    search_term = filters.get("search")
    if search_term:
        query = query.where(
            or_(
                Expense.title.ilike(f"%{search_term}%"),
                Expense.notes.ilike(f"%{search_term}%"),
            )
        )

    # Filters
    if filters.get("category_id"):
        query = query.where(Expense.category_id == filters["category_id"])

    if filters.get("date_from"):
        query = query.where(Expense.expense_date >= filters["date_from"])

    if filters.get("date_to"):
        query = query.where(Expense.expense_date <= filters["date_to"])

    if filters.get("amount_min") is not None:
        query = query.where(Expense.amount >= filters["amount_min"])

    if filters.get("amount_max") is not None:
        query = query.where(Expense.amount <= filters["amount_max"])

    if filters.get("payment_mode"):
        query = query.where(Expense.payment_mode == filters["payment_mode"])

    # Count total items
    count_query = select(func.count()).select_from(query.subquery())
    total_items_result = await db.execute(count_query)
    total_items = total_items_result.scalar_one()

    # Sorting
    sort_by = filters.get("sort_by", "date")
    sort_order = filters.get("sort_order", "desc")

    if sort_by == "amount":
        sort_col = Expense.amount
    elif sort_by == "category":
        sort_col = Category.name
    else:  # default to date
        sort_col = Expense.expense_date

    if sort_order == "asc":
        query = query.order_by(sort_col.asc(), Expense.created_at.asc())
    else:
        query = query.order_by(sort_col.desc(), Expense.created_at.desc())

    # Pagination
    query = query.offset(pagination["offset"]).limit(pagination["page_size"])

    # Execute
    result = await db.execute(query)
    items = result.scalars().all()

    total_pages = (
        math.ceil(total_items / pagination["page_size"]) if total_items > 0 else 0
    )

    return {
        "items": items,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
        "total_items": total_items,
        "total_pages": total_pages,
    }


async def get_expense_by_id(db: AsyncSession, expense_id: uuid.UUID) -> Expense:
    """Retrieve an expense by ID, raising NotFoundException if missing."""
    query = (
        select(Expense)
        .options(joinedload(Expense.category))
        .where(Expense.id == expense_id)
    )
    result = await db.execute(query)
    expense = result.scalar_one_or_none()
    if not expense:
        raise NotFoundException(f"Expense with ID {expense_id} not found", field="id")
    return expense


async def verify_budget_limit(
    db: AsyncSession,
    amount: Decimal,
    expense_date: date,
    category_id: uuid.UUID,
    exclude_expense_id: uuid.UUID | None = None,
) -> None:
    """Check if adding/updating this expense violates any overall or category budgets."""
    start_date, end_date = get_month_range(expense_date)
    normalized_month = expense_date.replace(day=1)

    # 1. Check overall budget
    overall_budget_query = select(Budget).where(
        Budget.scope == "overall",
        Budget.period_month == normalized_month,
    )
    overall_budget_result = await db.execute(overall_budget_query)
    overall_budget = overall_budget_result.scalar_one_or_none()

    if overall_budget:
        spent_query = select(func.sum(Expense.amount)).where(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
        )
        if exclude_expense_id:
            spent_query = spent_query.where(Expense.id != exclude_expense_id)

        spent_result = await db.execute(spent_query)
        current_spent = spent_result.scalar() or Decimal("0.00")

        if current_spent + amount > overall_budget.limit_amount:
            raise ValidationException(
                f"Expense amount of {amount} would exceed the overall monthly budget limit of {overall_budget.limit_amount} (current spent: {current_spent})",
                field="amount",
            )

    # 2. Check category budget
    category_budget_query = select(Budget).where(
        Budget.scope == "category",
        Budget.category_id == category_id,
        Budget.period_month == normalized_month,
    )
    category_budget_result = await db.execute(category_budget_query)
    category_budget = category_budget_result.scalar_one_or_none()

    if category_budget:
        cat_spent_query = select(func.sum(Expense.amount)).where(
            Expense.category_id == category_id,
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
        )
        if exclude_expense_id:
            cat_spent_query = cat_spent_query.where(Expense.id != exclude_expense_id)

        cat_spent_result = await db.execute(cat_spent_query)
        current_cat_spent = cat_spent_result.scalar() or Decimal("0.00")

        if current_cat_spent + amount > category_budget.limit_amount:
            raise ValidationException(
                f"Expense amount of {amount} would exceed the category monthly budget limit of {category_budget.limit_amount} (current spent: {current_cat_spent})",
                field="amount",
            )


async def create_expense(db: AsyncSession, schema: ExpenseCreate) -> Expense:
    """Create a new expense entry."""
    # Verify category exists
    category_check = await db.get(Category, schema.category_id)
    if not category_check:
        raise NotFoundException(
            f"Category with ID {schema.category_id} not found", field="category_id"
        )

    # Verify budget limit is not exceeded
    await verify_budget_limit(
        db,
        amount=schema.amount,
        expense_date=schema.expense_date,
        category_id=schema.category_id,
    )

    db_expense = Expense(
        title=schema.title,
        category_id=schema.category_id,
        amount=schema.amount,
        expense_date=schema.expense_date,
        notes=schema.notes,
        payment_mode=schema.payment_mode,
    )
    db.add(db_expense)
    await db.commit()

    # Reload with relation
    return await get_expense_by_id(db, db_expense.id)


async def update_expense(
    db: AsyncSession, expense_id: uuid.UUID, schema: ExpenseUpdate
) -> Expense:
    """Update properties of an existing expense."""
    expense = await get_expense_by_id(db, expense_id)

    # Check category existence if it is being updated
    category_id = expense.category_id
    if schema.category_id is not None and schema.category_id != expense.category_id:
        category_check = await db.get(Category, schema.category_id)
        if not category_check:
            raise NotFoundException(
                f"Category with ID {schema.category_id} not found", field="category_id"
            )
        category_id = schema.category_id

    # Determine amount and date to validate
    amount = schema.amount if schema.amount is not None else expense.amount
    expense_date = schema.expense_date if schema.expense_date is not None else expense.expense_date

    # Verify budget limit is not exceeded
    await verify_budget_limit(
        db,
        amount=amount,
        expense_date=expense_date,
        category_id=category_id,
        exclude_expense_id=expense_id,
    )

    # Update category_id
    if schema.category_id is not None:
        expense.category_id = schema.category_id

    # Update other fields if provided in request
    for field in ["title", "amount", "expense_date", "notes", "payment_mode"]:
        val = getattr(schema, field)
        if val is not None:
            setattr(expense, field, val)

    await db.commit()
    # Reload with relation
    return await get_expense_by_id(db, expense.id)


async def delete_expense(db: AsyncSession, expense_id: uuid.UUID) -> None:
    """Delete an expense entry."""
    expense = await get_expense_by_id(db, expense_id)
    await db.delete(expense)
    await db.commit()
