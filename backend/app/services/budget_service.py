import calendar
import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.budget import Budget
from app.models.category import Category
from app.models.expense import Expense
from app.schemas.budget import BudgetCreate, BudgetUpdate


def get_month_range(period_month: date) -> tuple[date, date]:
    """Helper to return the start and end dates of a month."""
    start_date = date(period_month.year, period_month.month, 1)
    _, last_day = calendar.monthrange(period_month.year, period_month.month)
    end_date = date(period_month.year, period_month.month, last_day)
    return start_date, end_date


async def get_budgets(
    db: AsyncSession, period_month: date | None = None
) -> list[Budget]:
    """Retrieve all budgets configured for a specific month (defaults to current month)."""
    if period_month is None:
        period_month = date.today().replace(day=1)
    else:
        period_month = period_month.replace(day=1)

    query = (
        select(Budget)
        .options(joinedload(Budget.category))
        .where(Budget.period_month == period_month)
        .order_by(Budget.scope.desc())  # overall budgets first
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_budget_by_id(db: AsyncSession, budget_id: uuid.UUID) -> Budget:
    """Retrieve a single budget by ID, raising NotFoundException if missing."""
    query = (
        select(Budget)
        .options(joinedload(Budget.category))
        .where(Budget.id == budget_id)
    )
    result = await db.execute(query)
    budget = result.scalar_one_or_none()
    if not budget:
        raise NotFoundException(f"Budget with ID {budget_id} not found", field="id")
    return budget


async def create_budget(db: AsyncSession, schema: BudgetCreate) -> Budget:
    """Create a new budget goal for overall or category scopes."""
    period_month = schema.period_month.replace(day=1)

    # Validation: Verify category exists if scope is category
    if schema.scope == "category":
        category_check = await db.get(Category, schema.category_id)
        if not category_check:
            raise NotFoundException(
                f"Category with ID {schema.category_id} not found", field="category_id"
            )

    # Check for uniqueness conflicts
    conflict_query = select(Budget).where(
        Budget.scope == schema.scope,
        Budget.period_month == period_month,
    )
    if schema.scope == "overall":
        conflict_query = conflict_query.where(Budget.category_id.is_(None))
    else:
        conflict_query = conflict_query.where(Budget.category_id == schema.category_id)

    conflict_result = await db.execute(conflict_query)
    if conflict_result.scalar_one_or_none():
        scope_str = (
            "overall" if schema.scope == "overall" else f"category {schema.category_id}"
        )
        raise ConflictException(
            f"Budget goal for {scope_str} already exists for {period_month.strftime('%Y-%m')}",
            field="period_month",
        )

    db_budget = Budget(
        scope=schema.scope,
        category_id=schema.category_id,
        period_month=period_month,
        limit_amount=schema.limit_amount,
    )
    db.add(db_budget)
    await db.commit()

    return await get_budget_by_id(db, db_budget.id)


async def update_budget(
    db: AsyncSession, budget_id: uuid.UUID, schema: BudgetUpdate
) -> Budget:
    """Update limit amount of an existing budget."""
    budget = await get_budget_by_id(db, budget_id)
    budget.limit_amount = schema.limit_amount
    await db.commit()
    await db.refresh(budget)
    return budget


async def delete_budget(db: AsyncSession, budget_id: uuid.UUID) -> None:
    """Delete a budget goal."""
    budget = await get_budget_by_id(db, budget_id)
    await db.delete(budget)
    await db.commit()


async def get_budgets_status(db: AsyncSession, period_month: date) -> list[dict]:
    """Calculate live spent, remaining, and warning status for all budgets in a month."""
    start_date, end_date = get_month_range(period_month)
    normalized_month = period_month.replace(day=1)

    # Fetch all budgets for this month
    budgets = await get_budgets(db, normalized_month)

    # Query overall spend in this month
    overall_spend_query = select(func.sum(Expense.amount)).where(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date,
    )
    overall_spend_result = await db.execute(overall_spend_query)
    overall_spent = overall_spend_result.scalar() or Decimal("0.00")

    # Query category-wise spends in this month
    category_spend_query = (
        select(Expense.category_id, func.sum(Expense.amount))
        .where(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
        )
        .group_by(Expense.category_id)
    )
    category_spend_result = await db.execute(category_spend_query)
    category_spends = {row[0]: (row[1] or Decimal("0.00")) for row in category_spend_result.all()}

    statuses = []
    for budget in budgets:
        # Determine spent amount
        if budget.scope == "overall":
            spent = overall_spent
        else:
            spent = category_spends.get(budget.category_id, Decimal("0.00"))

        limit = budget.limit_amount
        remaining = limit - spent

        # Determine warning status
        if spent > limit:
            status = "over_budget"
        elif spent >= limit * Decimal("0.9"):
            status = "near_limit"
        else:
            status = "on_track"

        statuses.append(
            {
                "id": budget.id,
                "scope": budget.scope,
                "category_id": budget.category_id,
                "category_name": budget.category.name if budget.category else None,
                "period_month": budget.period_month,
                "limit_amount": limit,
                "spent": spent,
                "remaining": remaining,
                "status": status,
            }
        )

    return statuses
