import calendar
import uuid
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.expense import Expense
from app.services.budget_service import get_budgets_status, get_month_range


async def get_summary(db: AsyncSession, user_id: uuid.UUID, period_month: date) -> dict:
    """Retrieve total monthly spend, recent expenses, and budget status snapshots for the user."""
    start_date, end_date = get_month_range(period_month)

    # 1. Total monthly spend for user
    total_query = select(func.sum(Expense.amount)).where(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date,
    )
    total_result = await db.execute(total_query)
    total_spent = total_result.scalar() or Decimal("0.00")

    # 2. Recent 5 expenses for user
    recent_query = (
        select(Expense)
        .options(joinedload(Expense.category))
        .where(Expense.user_id == user_id)
        .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
        .limit(5)
    )
    recent_result = await db.execute(recent_query)
    recent_expenses = recent_result.scalars().all()

    # 3. Budget status snapshot for user
    budgets_status = await get_budgets_status(db, user_id, period_month)

    return {
        "total_spent": total_spent,
        "recent_expenses": recent_expenses,
        "budgets_status": budgets_status,
    }


async def get_category_breakdown(
    db: AsyncSession,
    user_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    """Retrieve spending grouped by category for the user."""
    query = (
        select(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            func.sum(Expense.amount).label("total_spent"),
        )
        .join(Expense, Category.id == Expense.category_id)
        .where(Expense.user_id == user_id)
    )

    if date_from:
        query = query.where(Expense.expense_date >= date_from)
    if date_to:
        query = query.where(Expense.expense_date <= date_to)

    query = query.group_by(Category.id, Category.name).order_by(
        func.sum(Expense.amount).desc()
    )

    result = await db.execute(query)
    rows = result.all()

    # Calculate grand total to derive percentages
    grand_total = sum((row.total_spent or Decimal("0.00")) for row in rows)

    return [
        {
            "category_id": row.category_id,
            "category_name": row.category_name,
            "total_spent": row.total_spent or Decimal("0.00"),
            "percentage": float(round(((row.total_spent or Decimal("0.00")) / grand_total) * 100, 2)) if grand_total > 0 else 0.0,
        }
        for row in rows
    ]


async def get_spending_trend(
    db: AsyncSession,
    user_id: uuid.UUID,
    period: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    """Retrieve spending over time intervals for the user."""
    trunc_map = {"daily": "day", "weekly": "week", "monthly": "month"}
    trunc_val = trunc_map.get(period, "day")

    query = (
        select(
            func.date_trunc(trunc_val, Expense.expense_date).label("interval_date"),
            func.sum(Expense.amount).label("total_spent"),
        )
        .where(Expense.user_id == user_id)
    )

    if date_from:
        query = query.where(Expense.expense_date >= date_from)
    if date_to:
        query = query.where(Expense.expense_date <= date_to)

    query = query.group_by("interval_date").order_by("interval_date")

    result = await db.execute(query)
    return [
        {
            "date": row.interval_date.date() if row.interval_date else None,
            "total_spent": row.total_spent or Decimal("0.00"),
        }
        for row in result.all()
    ]


async def get_comparison(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Retrieve user's month-over-month total comparison and percentage change."""
    today = date.today()
    current_month_start, current_month_end = get_month_range(today)

    first_day_of_current = today.replace(day=1)
    last_day_of_prev = first_day_of_current - timedelta(days=1)
    prev_month_start, prev_month_end = get_month_range(last_day_of_prev)

    # Current month spend for user
    current_query = select(func.sum(Expense.amount)).where(
        Expense.user_id == user_id,
        Expense.expense_date >= current_month_start,
        Expense.expense_date <= current_month_end,
    )
    current_result = await db.execute(current_query)
    current_spent = current_result.scalar() or Decimal("0.00")

    # Previous month spend for user
    prev_query = select(func.sum(Expense.amount)).where(
        Expense.user_id == user_id,
        Expense.expense_date >= prev_month_start,
        Expense.expense_date <= prev_month_end,
    )
    prev_result = await db.execute(prev_query)
    prev_spent = prev_result.scalar() or Decimal("0.00")

    # Percentage change
    if prev_spent > Decimal("0.00"):
        percentage_change = ((current_spent - prev_spent) / prev_spent) * Decimal("100.00")
    else:
        percentage_change = Decimal("100.00") if current_spent > Decimal("0.00") else Decimal("0.00")

    return {
        "current_month_spent": current_spent,
        "previous_month_spent": prev_spent,
        "percentage_change": percentage_change,
    }


async def get_top_categories(db: AsyncSession, user_id: uuid.UUID, limit: int = 5) -> list[dict]:
    """Retrieve user's ranked categories by spending."""
    today = date.today()
    start_date, end_date = get_month_range(today)

    query = (
        select(
            Category.name.label("category_name"),
            func.sum(Expense.amount).label("total_spent"),
        )
        .join(Expense, Category.id == Expense.category_id)
        .where(
            Expense.user_id == user_id,
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
        )
        .group_by(Category.name)
        .order_by(func.sum(Expense.amount).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return [
        {
            "category_name": row.category_name,
            "total_spent": row.total_spent or Decimal("0.00"),
        }
        for row in result.all()
    ]


async def get_average_spend(db: AsyncSession, user_id: uuid.UUID, basis: str) -> dict:
    """Retrieve user's average daily/weekly spend in current month."""
    today = date.today()
    start_date, end_date = get_month_range(today)

    query = select(func.sum(Expense.amount)).where(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date,
    )
    result = await db.execute(query)
    current_spent = result.scalar() or Decimal("0.00")

    days_elapsed = today.day
    if basis == "daily":
        average = current_spent / Decimal(str(days_elapsed))
    else:
        weeks_elapsed = Decimal(str(days_elapsed)) / Decimal("7.0")
        average = current_spent / weeks_elapsed

    return {
        "basis": basis,
        "average_spent": average,
        "days_elapsed": days_elapsed,
        "current_month_spent": current_spent,
    }


async def get_payment_mode_breakdown(
    db: AsyncSession,
    user_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    """Retrieve user's spending grouped by payment mode."""
    query = select(
        Expense.payment_mode.label("payment_mode"),
        func.sum(Expense.amount).label("total_spent"),
    ).where(
        Expense.user_id == user_id,
        Expense.payment_mode.isnot(None),
    )

    if date_from:
        query = query.where(Expense.expense_date >= date_from)
    if date_to:
        query = query.where(Expense.expense_date <= date_to)

    query = query.group_by(Expense.payment_mode).order_by(
        func.sum(Expense.amount).desc()
    )

    result = await db.execute(query)
    rows = result.all()

    grand_total = sum((row.total_spent or Decimal("0.00")) for row in rows)

    return [
        {
            "payment_mode": row.payment_mode,
            "total_spent": row.total_spent or Decimal("0.00"),
            "percentage": float(round(((row.total_spent or Decimal("0.00")) / grand_total) * 100, 2)) if grand_total > 0 else 0.0,
        }
        for row in rows
    ]
