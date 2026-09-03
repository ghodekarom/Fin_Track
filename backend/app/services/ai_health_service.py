import calendar
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.llm import get_llm_provider
from app.models.budget import Budget
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.schemas.ai import (
    FinancialHealthScoreResponse,
    ScorePillarBreakdown,
)

logger = logging.getLogger("fintrack.ai.health")


async def calculate_monthly_financial_health(
    db: AsyncSession,
    user: User,
) -> FinancialHealthScoreResponse:
    """
    Computes deterministic 0-100 Financial Health Score across 3 core pillars
    (Budget Adherence, Savings Velocity, Category Discipline) and generates
    an Executive Summary / Monthly AI Digest.
    """
    now = datetime.now(timezone.utc).date()
    current_month_start = date(now.year, now.month, 1)
    period_month_str = now.strftime("%B %Y")
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_elapsed = max(1, now.day)

    # 1. Fetch expenses for current month
    exp_query = (
        select(Expense, Category.name.label("category_name"))
        .outerjoin(Category, Expense.category_id == Category.id)
        .where(
            Expense.user_id == user.id,
            Expense.expense_date >= current_month_start,
        )
    )
    res = await db.execute(exp_query)
    month_expenses = res.all()

    total_spent = 0.0
    cat_spend: Dict[str, float] = {}
    for exp, cat_name in month_expenses:
        amt = float(exp.amount)
        total_spent += amt
        c = cat_name or "Other"
        cat_spend[c] = cat_spend.get(c, 0.0) + amt

    # 2. Fetch overall budget
    b_query = select(Budget).where(
        Budget.user_id == user.id,
        Budget.period_month == current_month_start,
        Budget.scope == "overall",
    )
    b_res = await db.execute(b_query)
    overall_b = b_res.scalar_one_or_none()
    budget_limit = float(overall_b.limit_amount) if overall_b else None

    # -------------------------------------------------------------
    # Pillar 1: Budget Adherence (0 - 40 points)
    # -------------------------------------------------------------
    if budget_limit and budget_limit > 0:
        utilization = total_spent / budget_limit
        if utilization <= 0.80:
            budget_pts = 40.0
        elif utilization <= 1.0:
            budget_pts = 40.0 - ((utilization - 0.80) / 0.20 * 15.0)  # 25 to 40
        elif utilization <= 1.20:
            budget_pts = max(5.0, 25.0 - ((utilization - 1.0) / 0.20 * 15.0))  # 10 to 25
        else:
            budget_pts = max(0.0, 10.0 - ((utilization - 1.20) * 20.0))
    else:
        budget_pts = 25.0  # Baseline when no ceiling set

    # -------------------------------------------------------------
    # Pillar 2: Savings Velocity & Burn Control (0 - 35 points)
    # -------------------------------------------------------------
    burn_rate = total_spent / days_elapsed
    projected_spend = total_spent + (burn_rate * (days_in_month - days_elapsed))

    if budget_limit and budget_limit > 0:
        savings_ratio = max(0.0, (budget_limit - projected_spend) / budget_limit)
        if savings_ratio >= 0.25:
            savings_pts = 35.0
        elif savings_ratio >= 0.10:
            savings_pts = 25.0 + ((savings_ratio - 0.10) / 0.15 * 10.0)
        elif savings_ratio > 0:
            savings_pts = 15.0 + (savings_ratio / 0.10 * 10.0)
        else:
            savings_pts = max(5.0, 15.0 - (abs(savings_ratio) * 20.0))
    else:
        savings_pts = 22.0

    # -------------------------------------------------------------
    # Pillar 3: Category Discipline & Diversification (0 - 25 points)
    # -------------------------------------------------------------
    top_cat = "None"
    top_amt = 0.0
    top_pct = 0.0

    if cat_spend and total_spent > 0:
        top_cat, top_amt = max(cat_spend.items(), key=lambda x: x[1])
        top_pct = top_amt / total_spent

    if top_pct <= 0.35:
        category_pts = 25.0  # Well balanced
    elif top_pct <= 0.50:
        category_pts = 18.0
    elif top_pct <= 0.70:
        category_pts = 12.0
    else:
        category_pts = 6.0  # Extreme concentration

    # Total Score
    total_score = int(round(budget_pts + savings_pts + category_pts))
    total_score = max(0, min(100, total_score))

    # Letter Grade & Label
    if total_score >= 88:
        grade = "A+"
        label = "Elite Financial Health"
    elif total_score >= 78:
        grade = "A"
        label = "Healthy & Disciplined"
    elif total_score >= 68:
        grade = "B"
        label = "Good Progress"
    elif total_score >= 50:
        grade = "C"
        label = "Needs Attention"
    else:
        grade = "D"
        label = "At Risk"

    # Achievements & Goals
    achievements = []
    goals = []

    if budget_pts >= 30:
        achievements.append(f"Strong budget discipline: Keeping spend well within target limits.")
    if top_pct <= 0.40 and total_spent > 0:
        achievements.append(f"Well-diversified portfolio: No single category dominates spending.")
    if savings_pts >= 25:
        achievements.append(f"Positive savings velocity: On track to preserve meaningful monthly surplus.")
    if not achievements:
        achievements.append("Consistent expense logging: Built active financial visibility.")

    if top_pct > 0.30:
        goals.append(f"Trim {top_cat} spending by 10-15% next month to improve diversification.")
    if not budget_limit:
        goals.append("Set an overall monthly budget ceiling to unlock maximum adherence points.")
    else:
        goals.append("Maintain safe daily spend velocity through month-end.")

    # Executive Summary paragraph
    exec_summary = (
        f"For {period_month_str}, you scored a Financial Health Index of {total_score}/100 ({grade} — {label}). "
        f"You have logged ₹{total_spent:,.0f} across {len(month_expenses)} transactions, with {top_cat} being your largest focus ({round(top_pct * 100, 1)}% of spend). "
        f"{'You are comfortably within budget limits.' if budget_pts >= 25 else 'Focusing on curbing discretionary spikes will rapidly elevate your score.'}"
    )

    # 3. Try LLM enrichment for executive digest
    llm = get_llm_provider()
    provider_label = "Deterministic Health Engine"

    if llm and total_spent > 0:
        system_instruction = (
            "You are FinTrack AI's Executive Financial Analyst. "
            "Write a concise, polished 2-sentence executive summary for the user's monthly financial health digest, "
            "highlighting their score, key achievement, and strategic tip. "
            "Return JSON matching {'executive_summary': string}."
        )
        try:
            res_json = await llm.generate_structured_json(
                system_instruction=system_instruction,
                prompt=(
                    f"User scored {total_score}/100 ({grade} - {label}) for {period_month_str}. "
                    f"Total Spend: ₹{total_spent:,.0f}. Overall Budget: {f'₹{budget_limit:,.0f}' if budget_limit else 'None'}. "
                    f"Top Category: {top_cat} (₹{top_amt:,.0f}). Pillar Scores: Adherence={budget_pts}/40, "
                    f"Savings={savings_pts}/35, Discipline={category_pts}/25."
                ),
            )
            if res_json.get("executive_summary"):
                exec_summary = res_json["executive_summary"]
                provider_label = f"Gemini ({settings.AI_MODEL_NAME})"
        except Exception as exc:
            logger.warning(f"Health score LLM enrichment error: {exc}. Using deterministic summary.")

    return FinancialHealthScoreResponse(
        health_score=total_score,
        letter_grade=grade,
        status_label=label,
        pillars=ScorePillarBreakdown(
            budget_adherence=round(budget_pts, 1),
            savings_velocity=round(savings_pts, 1),
            category_discipline=round(category_pts, 1),
        ),
        executive_summary=exec_summary,
        key_achievements=achievements,
        improvement_goals=goals,
        top_spend_category=top_cat,
        potential_monthly_savings=round(max(0.0, top_amt * 0.15), 2),
        period_month=period_month_str,
        generated_at=datetime.now(timezone.utc),
        provider=provider_label,
    )
