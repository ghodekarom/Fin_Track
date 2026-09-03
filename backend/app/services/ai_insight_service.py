import asyncio
from datetime import date, datetime, timedelta, timezone
import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.llm import get_llm_provider
from app.models.budget import Budget
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.schemas.ai import (
    InsightCategory,
    SpendingInsight,
    SpendingInsightsResponse,
)

logger = logging.getLogger("fintrack.ai")

# Thread-safe in-memory cache: user_id -> (timestamp, SpendingInsightsResponse)
_INSIGHTS_CACHE: Dict[UUID, Tuple[datetime, SpendingInsightsResponse]] = {}


async def _fetch_user_financial_data(
    db: AsyncSession, user_id: UUID
) -> Dict[str, any]:
    """
    Fetch and aggregate user financial data strictly scoped to current_user.id.
    Zero cross-user leakage.
    """
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    # 1. Fetch expenses for last 60 days
    query = (
        select(Expense, Category.name.label("category_name"))
        .outerjoin(Category, Expense.category_id == Category.id)
        .where(
            Expense.user_id == user_id,
            Expense.expense_date >= sixty_days_ago.date(),
        )
        .order_by(Expense.expense_date.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    last_30_expenses = []
    prev_30_expenses = []

    for expense, cat_name in rows:
        exp_dict = {
            "amount": float(expense.amount),
            "category": cat_name or "Uncategorized",
            "date": str(expense.expense_date),
            "description": expense.title or expense.notes or "",
            "payment_method": expense.payment_mode or "other",
        }
        # Parse date
        exp_date = expense.expense_date
        if hasattr(exp_date, "date"):
            exp_date = exp_date.date()

        if exp_date >= thirty_days_ago.date():
            last_30_expenses.append(exp_dict)
        else:
            prev_30_expenses.append(exp_dict)

    # 2. Category totals for last 30 days
    cat_totals: Dict[str, float] = {}
    total_last_30 = 0.0
    weekend_spend = 0.0

    for exp in last_30_expenses:
        amt = exp["amount"]
        cat = exp["category"]
        total_last_30 += amt
        cat_totals[cat] = cat_totals.get(cat, 0.0) + amt

        # Check day of week for weekend calculation (5=Sat, 6=Sun)
        try:
            d = datetime.strptime(exp["date"][:10], "%Y-%m-%d")
            if d.weekday() in (5, 6):
                weekend_spend += amt
        except Exception:
            pass

    total_prev_30 = sum(exp["amount"] for exp in prev_30_expenses)

    # 3. Active Budgets
    current_month_start = date(now.year, now.month, 1)
    budget_query = (
        select(Budget, Category.name.label("category_name"))
        .outerjoin(Category, Budget.category_id == Category.id)
        .where(
            Budget.user_id == user_id,
            Budget.period_month == current_month_start,
        )
    )
    budget_rows = (await db.execute(budget_query)).all()

    budget_status = []
    for b, cat_name in budget_rows:
        cat_label = cat_name or "Overall"
        limit_amt = float(b.limit_amount)
        spent = cat_totals.get(cat_label, 0.0) if cat_name else total_last_30
        ratio = (spent / limit_amt) if limit_amt > 0 else 0
        budget_status.append({
            "category": cat_label,
            "limit": limit_amt,
            "spent": spent,
            "percentage": round(ratio * 100, 1),
            "is_over": spent > limit_amt,
        })

    # 4. Recurring subscriptions detection (approx monthly frequency)
    recurring_charges = []
    seen_descriptions: Dict[str, List[float]] = {}
    for exp in last_30_expenses + prev_30_expenses:
        desc = exp["description"].strip().lower()
        if len(desc) >= 3:
            seen_descriptions.setdefault(desc, []).append(exp["amount"])

    for desc, amounts in seen_descriptions.items():
        if len(amounts) >= 2 and max(amounts) - min(amounts) < 50:
            recurring_charges.append({
                "description": desc.title(),
                "average_amount": round(sum(amounts) / len(amounts), 2),
            })

    return {
        "total_last_30": round(total_last_30, 2),
        "total_prev_30": round(total_prev_30, 2),
        "count_last_30": len(last_30_expenses),
        "category_breakdown": {k: round(v, 2) for k, v in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)},
        "weekend_spend_ratio": round((weekend_spend / total_last_30 * 100), 1) if total_last_30 > 0 else 0,
        "budgets": budget_status,
        "recurring_charges": recurring_charges[:5],
    }


def _generate_deterministic_insights(data: Dict[str, any]) -> List[SpendingInsight]:
    """
    Intelligent rule-based financial insights engine.
    Runs when LLM provider is unconfigured, rate-limited, or offline.
    """
    insights: List[SpendingInsight] = []
    total_spent = data["total_last_30"]
    categories = data["category_breakdown"]
    budgets = data["budgets"]
    recurring = data["recurring_charges"]
    weekend_ratio = data["weekend_spend_ratio"]

    # 1. Budget Alerts
    for b in budgets:
        if b["is_over"]:
            overage = round(b["spent"] - b["limit"], 2)
            insights.append(
                SpendingInsight(
                    id=f"budget-over-{b['category'].lower().replace(' ', '-')}",
                    type=InsightCategory.BUDGET_ALERT,
                    title=f"Budget Exceeded in {b['category']}",
                    description=f"You have spent ₹{b['spent']:,.0f}, exceeding your ₹{b['limit']:,.0f} limit by ₹{overage:,.0f} ({b['percentage']}% utilized).",
                    potential_savings=overage,
                    action_tip=f"Pause non-essential expenses in {b['category']} for the remainder of this month.",
                    impact_level="high",
                )
            )
        elif b["percentage"] >= 80:
            insights.append(
                SpendingInsight(
                    id=f"budget-warn-{b['category'].lower().replace(' ', '-')}",
                    type=InsightCategory.BUDGET_ALERT,
                    title=f"{b['category']} Budget Near Limit",
                    description=f"You've consumed {b['percentage']}% of your ₹{b['limit']:,.0f} budget with ₹{b['limit'] - b['spent']:,.0f} remaining.",
                    potential_savings=None,
                    action_tip=f"Slow down spending in {b['category']} to stay within your monthly target.",
                    impact_level="medium",
                )
            )

    # 2. High Category Concentration (Discretionary Categories)
    discretionary = ["Food & Dining", "Shopping", "Entertainment", "Travel"]
    for cat, amt in categories.items():
        if total_spent > 0:
            pct = (amt / total_spent) * 100
            if cat in discretionary and pct >= 30:
                est_savings = round(amt * 0.15, 2)  # 15% reduction target
                insights.append(
                    SpendingInsight(
                        id=f"category-high-{cat.lower().replace(' ', '-')}",
                        type=InsightCategory.HIGH_IMPACT,
                        title=f"High Spend Concentration in {cat}",
                        description=f"{cat} accounts for {pct:.1f}% of your total expenses this month (₹{amt:,.0f}).",
                        potential_savings=est_savings,
                        action_tip=f"Aiming for a 15% reduction in {cat} could save you approximately ₹{est_savings:,.0f} next month.",
                        impact_level="high",
                    )
                )

    # 3. Recurring Subscriptions
    if recurring:
        sub_total = sum(r["average_amount"] for r in recurring)
        names = ", ".join(r["description"] for r in recurring[:3])
        insights.append(
            SpendingInsight(
                id="recurring-subscriptions-detected",
                type=InsightCategory.SUBSCRIPTION,
                title="Active Recurring Subscriptions Detected",
                description=f"Identified {len(recurring)} regular charges totaling ~₹{sub_total:,.0f}/month including {names}.",
                potential_savings=round(sub_total * 0.3, 2),  # canceling 1 unneeded
                action_tip="Audit your recurring subscriptions and cancel any service you haven't used in the past 30 days.",
                impact_level="medium",
            )
        )

    # 4. Weekend Spending Surge
    if weekend_ratio >= 45 and total_spent > 2000:
        insights.append(
            SpendingInsight(
                id="weekend-spending-spike",
                type=InsightCategory.QUICK_WIN,
                title="Weekend Spending Surge",
                description=f"Weekends account for {weekend_ratio:.1f}% of your monthly expenses despite being only 2 out of 7 days.",
                potential_savings=round(total_spent * 0.08, 2),
                action_tip="Try setting a weekend leisure allowance to avoid impulse out-of-home spending.",
                impact_level="medium",
            )
        )

    # 5. Fallback Starter Tip if user has very few expenses
    if not insights:
        if total_spent > 0:
            insights.append(
                SpendingInsight(
                    id="spending-healthy",
                    type=InsightCategory.QUICK_WIN,
                    title="Spending Well Balanced",
                    description=f"You have tracked ₹{total_spent:,.0f} across {data['count_last_30']} transactions. Your spending looks well-distributed across categories.",
                    potential_savings=round(total_spent * 0.05, 2),
                    action_tip="Set monthly budget targets for your primary categories to unlock personalized progress tracking.",
                    impact_level="low",
                )
            )
        else:
            insights.append(
                SpendingInsight(
                    id="get-started-tracking",
                    type=InsightCategory.QUICK_WIN,
                    title="Start Logging Daily Expenses",
                    description="As you add expenses and configure category budgets, FinTrack AI will automatically unlock personalized savings opportunities and habit audits.",
                    potential_savings=None,
                    action_tip="Add your first 3 expenses this week to unlock smart financial insights.",
                    impact_level="low",
                )
            )

    return insights[:4]


async def get_user_spending_insights(
    db: AsyncSession,
    user: User,
    force_refresh: bool = False,
) -> SpendingInsightsResponse:
    """
    Get personalized AI spending insights for the authenticated user.
    Uses cached result if available and unexpired, unless force_refresh=True.
    """
    now = datetime.now(timezone.utc)
    cache_entry = _INSIGHTS_CACHE.get(user.id)

    # Check cache validity
    if not force_refresh and cache_entry:
        cached_time, cached_response = cache_entry
        cache_expiry = timedelta(minutes=settings.AI_INSIGHTS_CACHE_MINUTES)
        if now - cached_time < cache_expiry:
            return SpendingInsightsResponse(
                insights=cached_response.insights,
                total_potential_monthly_savings=cached_response.total_potential_monthly_savings,
                currency="INR",
                generated_at=cached_response.generated_at,
                provider=cached_response.provider,
                is_cached=True,
            )

    # 1. Aggregate user financial data
    financial_data = await _fetch_user_financial_data(db, user.id)

    # 2. Try Google Gemini LLM provider if configured
    llm = get_llm_provider()
    insights: List[SpendingInsight] = []
    provider_name = "Rule-based Engine"

    if llm and financial_data["total_last_30"] > 0:
        system_instruction = (
            "You are FinTrack's Senior AI Personal Finance Advisor. "
            "Analyze the user's spending data and produce 3 to 4 personalized, encouraging, and actionable insights. "
            "Categories must be strictly one of: 'quick_win', 'budget_alert', 'subscription', 'high_impact'. "
            "All amounts are in Indian Rupees (INR). Return strictly JSON matching the required structure."
        )

        prompt = (
            f"User Financial Summary (Last 30 Days):\n"
            f"- Total Expenditure: ₹{financial_data['total_last_30']}\n"
            f"- Previous Month Expenditure: ₹{financial_data['total_prev_30']}\n"
            f"- Category Breakdown: {financial_data['category_breakdown']}\n"
            f"- Weekend Spending Share: {financial_data['weekend_spend_ratio']}%\n"
            f"- Active Budgets: {financial_data['budgets']}\n"
            f"- Identified Recurring Charges: {financial_data['recurring_charges']}\n\n"
            f"Generate a JSON object with an 'insights' array where each object has:\n"
            f"- 'id': string\n"
            f"- 'type': one of ['quick_win', 'budget_alert', 'subscription', 'high_impact']\n"
            f"- 'title': short catchy title (max 10 words)\n"
            f"- 'description': clear 1-2 sentence breakdown\n"
            f"- 'potential_savings': estimated monthly numeric savings amount in INR (or null)\n"
            f"- 'action_tip': 1 specific concrete action the user should take\n"
            f"- 'impact_level': 'high' | 'medium' | 'low'\n"
        )

        try:
            response_json = await llm.generate_structured_json(
                system_instruction=system_instruction,
                prompt=prompt,
            )
            raw_insights = response_json.get("insights", [])
            for item in raw_insights:
                try:
                    insight_type = InsightCategory(item.get("type", "quick_win"))
                except ValueError:
                    insight_type = InsightCategory.QUICK_WIN

                insights.append(
                    SpendingInsight(
                        id=str(item.get("id") or f"gemini-{len(insights)}"),
                        type=insight_type,
                        title=str(item.get("title", "Spending Insight")),
                        description=str(item.get("description", "")),
                        potential_savings=float(item["potential_savings"]) if item.get("potential_savings") else None,
                        action_tip=str(item.get("action_tip", "")),
                        impact_level=item.get("impact_level", "medium"),
                    )
                )
            if insights:
                provider_name = f"Gemini ({settings.AI_MODEL_NAME})"
        except Exception as exc:
            logger.warning(f"Gemini generation fallback triggered: {exc}")
            insights = []

    # 3. Fallback to deterministic statistical engine if LLM was skipped or returned empty
    if not insights:
        insights = _generate_deterministic_insights(financial_data)
        provider_name = "Rule-based Engine"

    # Compute total potential savings
    total_savings = sum(i.potential_savings for i in insights if i.potential_savings is not None)

    response = SpendingInsightsResponse(
        insights=insights,
        total_potential_monthly_savings=round(total_savings, 2),
        currency="INR",
        generated_at=now,
        provider=provider_name,
        is_cached=False,
    )

    # Update cache
    _INSIGHTS_CACHE[user.id] = (now, response)
    return response
