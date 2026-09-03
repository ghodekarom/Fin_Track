import calendar
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.schemas.ai import (
    CategoryVelocityForecast,
    DynamicBudgetRecommendation,
    OverallVelocityForecast,
    PredictiveBudgetResponse,
    VelocityRiskLevel,
)

logger = logging.getLogger("fintrack.ai.budget")


async def get_predictive_budget_forecast(
    db: AsyncSession,
    user: User,
) -> PredictiveBudgetResponse:
    """
    Computes real-time spending velocity, projected month-end burn rate,
    day-of-exhaustion prediction, safe daily spend, and smart budget allocations.
    Strictly isolated to user.id.
    """
    now_dt = datetime.now(timezone.utc)
    today = now_dt.date()
    current_month_start = date(today.year, today.month, 1)
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_elapsed = max(1, today.day)
    days_remaining = max(1, days_in_month - today.day + 1)

    # 1. Fetch current month expenses
    exp_query = (
        select(Expense, Category.name.label("category_name"))
        .outerjoin(Category, Expense.category_id == Category.id)
        .where(
            Expense.user_id == user.id,
            Expense.expense_date >= current_month_start,
            Expense.expense_date <= today,
        )
    )
    exp_result = await db.execute(exp_query)
    current_month_expenses = exp_result.all()

    total_current_spent = 0.0
    cat_spent_map: Dict[str, float] = {}

    for exp, cat_name in current_month_expenses:
        amt = float(exp.amount)
        total_current_spent += amt
        cat_id_str = str(exp.category_id)
        cat_spent_map[cat_id_str] = cat_spent_map.get(cat_id_str, 0.0) + amt

    # 2. Fetch current month budgets
    budget_query = (
        select(Budget, Category.name.label("category_name"))
        .outerjoin(Category, Budget.category_id == Category.id)
        .where(
            Budget.user_id == user.id,
            Budget.period_month == current_month_start,
        )
    )
    budget_result = await db.execute(budget_query)
    budgets = budget_result.all()

    overall_budget_limit: Optional[float] = None
    category_forecasts: List[CategoryVelocityForecast] = []

    for b, cat_name in budgets:
        limit_amt = float(b.limit_amount)
        if b.scope == "overall" or b.category_id is None:
            overall_budget_limit = limit_amt
            continue

        cat_id_str = str(b.category_id)
        c_spent = cat_spent_map.get(cat_id_str, 0.0)
        c_burn = c_spent / days_elapsed
        c_projected = c_spent + (c_burn * (days_remaining - 1))
        c_overage = max(0.0, c_projected - limit_amt)
        c_remaining = max(0.0, limit_amt - c_spent)
        c_safe_daily = c_remaining / days_remaining

        c_exhaustion_day: Optional[int] = None
        if c_burn > 0:
            est_day = int(limit_amt / c_burn)
            if est_day <= days_in_month:
                c_exhaustion_day = max(1, est_day)

        if c_spent >= limit_amt:
            c_risk = VelocityRiskLevel.CRITICAL
        elif c_projected > limit_amt:
            c_risk = VelocityRiskLevel.MODERATE if (c_exhaustion_day and c_exhaustion_day > today.day + 5) else VelocityRiskLevel.CRITICAL
        else:
            c_risk = VelocityRiskLevel.SAFE

        category_forecasts.append(
            CategoryVelocityForecast(
                category_id=cat_id_str,
                category_name=cat_name or "Category",
                budget_limit=limit_amt,
                current_spent=round(c_spent, 2),
                daily_burn_rate=round(c_burn, 2),
                projected_month_end_spend=round(c_projected, 2),
                projected_overage=round(c_overage, 2),
                exhaustion_day=c_exhaustion_day,
                risk_level=c_risk,
                safe_daily_spend=round(c_safe_daily, 2),
            )
        )

    # 3. Overall Velocity Calculations
    overall_burn = total_current_spent / days_elapsed
    overall_projected = total_current_spent + (overall_burn * (days_remaining - 1))

    if overall_budget_limit and overall_budget_limit > 0:
        overall_remaining = max(0.0, overall_budget_limit - total_current_spent)
        overall_safe_daily = overall_remaining / days_remaining
        overall_overage = max(0.0, overall_projected - overall_budget_limit)

        overall_exhaustion_day: Optional[int] = None
        if overall_burn > 0:
            est_day = int(overall_budget_limit / overall_burn)
            if est_day <= days_in_month:
                overall_exhaustion_day = max(1, est_day)

        if total_current_spent >= overall_budget_limit:
            overall_risk = VelocityRiskLevel.CRITICAL
            overall_message = f"Budget limit of ₹{overall_budget_limit:,.0f} already exceeded by ₹{total_current_spent - overall_budget_limit:,.0f}."
        elif overall_projected > overall_budget_limit:
            overall_risk = VelocityRiskLevel.CRITICAL if (overall_exhaustion_day and overall_exhaustion_day <= today.day + 7) else VelocityRiskLevel.MODERATE
            overall_message = (
                f"At your current pace of ₹{overall_burn:,.0f}/day, you are projected to exhaust your budget "
                f"by Day {overall_exhaustion_day} ({days_in_month - overall_exhaustion_day} days early)."
            )
        else:
            overall_risk = VelocityRiskLevel.SAFE
            overall_message = f"Spending pace is controlled! Your safe daily spending limit is ₹{overall_safe_daily:,.0f}/day."
    else:
        overall_safe_daily = 0.0
        overall_overage = 0.0
        overall_risk = VelocityRiskLevel.SAFE
        overall_message = f"You are spending approximately ₹{overall_burn:,.0f}/day with no overall budget limit set."

    overall_velocity = OverallVelocityForecast(
        overall_budget_limit=overall_budget_limit,
        current_spent=round(total_current_spent, 2),
        daily_burn_rate=round(overall_burn, 2),
        projected_month_end_spend=round(overall_projected, 2),
        projected_overage=round(overall_overage, 2),
        days_elapsed=days_elapsed,
        days_remaining=days_remaining,
        safe_daily_spend=round(overall_safe_daily, 2),
        risk_level=overall_risk,
        risk_message=overall_message,
        category_forecasts=sorted(category_forecasts, key=lambda x: (x.risk_level == VelocityRiskLevel.CRITICAL, x.projected_overage), reverse=True),
    )

    # 4. Smart Budget Allocator (Historical Category Average Analysis)
    sixty_days_ago = today - timedelta(days=60)
    hist_query = (
        select(Category.id, Category.name, func.sum(Expense.amount), func.count(Expense.id))
        .join(Expense, Expense.category_id == Category.id)
        .where(
            Expense.user_id == user.id,
            Expense.expense_date >= sixty_days_ago,
        )
        .group_by(Category.id, Category.name)
    )
    hist_result = await db.execute(hist_query)
    hist_rows = hist_result.all()

    # Map current category budgets for comparison
    cat_budget_map = {str(b.category_id): float(b.limit_amount) for b, _ in budgets if b.category_id}

    smart_allocations: List[DynamicBudgetRecommendation] = []
    for cat_id, cat_name, sum_amt, count in hist_rows:
        total_hist = float(sum_amt or 0)
        # Approximate 2-month span
        avg_monthly = total_hist / 2.0 if total_hist > 0 else 0.0
        current_b = cat_budget_map.get(str(cat_id))

        # Suggested budget = average rounded up to nearest 500 with a 5% buffer
        if avg_monthly > 0:
            suggested = max(1000.0, round((avg_monthly * 1.05) / 500.0) * 500.0)
        else:
            suggested = 2500.0

        if current_b:
            diff = suggested - current_b
            if abs(diff) < 250:
                reasoning = f"Your current limit of ₹{current_b:,.0f} aligns well with your 2-month average of ₹{avg_monthly:,.0f}."
            elif diff > 0:
                reasoning = f"You regularly spend ~₹{avg_monthly:,.0f}/mo. Increasing from ₹{current_b:,.0f} to ₹{suggested:,.0f} creates a realistic ceiling."
            else:
                reasoning = f"You are spending less than your limit (avg ₹{avg_monthly:,.0f}/mo). Trimming to ₹{suggested:,.0f} frees up budget."
        else:
            reasoning = f"Based on your recent spending (~₹{avg_monthly:,.0f}/mo), setting a ₹{suggested:,.0f} limit keeps this category in check."

        smart_allocations.append(
            DynamicBudgetRecommendation(
                category_id=str(cat_id),
                category_name=cat_name,
                current_budget=current_b,
                suggested_budget=suggested,
                average_monthly_spend=round(avg_monthly, 2),
                reasoning=reasoning,
            )
        )

    return PredictiveBudgetResponse(
        velocity=overall_velocity,
        smart_allocations=sorted(smart_allocations, key=lambda x: x.average_monthly_spend, reverse=True),
        currency="INR",
        generated_at=now_dt,
    )


async def apply_suggested_budget(
    db: AsyncSession,
    user: User,
    category_id: UUID,
    amount: float,
) -> Budget:
    """
    1-click apply an AI-recommended budget for the current month.
    """
    today = datetime.now(timezone.utc).date()
    current_month_start = date(today.year, today.month, 1)

    # Check if budget already exists for this category this month
    query = select(Budget).where(
        Budget.user_id == user.id,
        Budget.scope == "category",
        Budget.category_id == category_id,
        Budget.period_month == current_month_start,
    )
    res = await db.execute(query)
    existing_budget = res.scalar_one_or_none()

    if existing_budget:
        existing_budget.limit_amount = Decimal(str(amount))
        await db.commit()
        await db.refresh(existing_budget)
        return existing_budget
    else:
        new_budget = Budget(
            user_id=user.id,
            scope="category",
            category_id=category_id,
            limit_amount=Decimal(str(amount)),
            period_month=current_month_start,
        )
        db.add(new_budget)
        await db.commit()
        await db.refresh(new_budget)
        return new_budget
