import calendar
from datetime import date, datetime, timedelta, timezone
import logging
import re
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
    AskAiQueryRequest,
    AskAiQueryResponse,
    ChatMessage,
)

logger = logging.getLogger("fintrack.ai.assistant")


async def _gather_assistant_financial_context(
    db: AsyncSession,
    user_id: UUID,
) -> Dict[str, Any]:
    """
    Gather financial context for the authenticated user to ground the AI's responses.
    Strictly scoped to user_id.
    """
    now = datetime.now(timezone.utc).date()
    current_month_start = date(now.year, now.month, 1)
    sixty_days_ago = now - timedelta(days=60)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_elapsed = max(1, now.day)
    days_remaining = max(1, days_in_month - now.day + 1)

    # 1. Fetch expenses for last 60 days
    query = (
        select(Expense, Category.name.label("category_name"))
        .outerjoin(Category, Expense.category_id == Category.id)
        .where(
            Expense.user_id == user_id,
            Expense.expense_date >= sixty_days_ago,
        )
        .order_by(Expense.expense_date.desc())
    )
    res = await db.execute(query)
    all_expenses = res.all()

    current_month_expenses = []
    prev_month_expenses = []
    cat_totals: Dict[str, float] = {}
    largest_expense = None
    max_amount = 0.0

    for exp, cat_name in all_expenses:
        amt = float(exp.amount)
        c_name = cat_name or "Uncategorized"
        item = {
            "title": exp.title,
            "category": c_name,
            "amount": amt,
            "date": str(exp.expense_date),
            "payment_mode": exp.payment_mode or "other",
            "notes": exp.notes or "",
        }

        if exp.expense_date >= current_month_start:
            current_month_expenses.append(item)
            cat_totals[c_name] = cat_totals.get(c_name, 0.0) + amt
            if amt > max_amount:
                max_amount = amt
                largest_expense = item
        else:
            prev_month_expenses.append(item)

    total_spent_this_month = sum(e["amount"] for e in current_month_expenses)
    total_spent_prev_month = sum(e["amount"] for e in prev_month_expenses)

    # 2. Fetch budgets for current month
    budget_query = (
        select(Budget, Category.name.label("category_name"))
        .outerjoin(Category, Budget.category_id == Category.id)
        .where(
            Budget.user_id == user_id,
            Budget.period_month == current_month_start,
        )
    )
    budget_res = await db.execute(budget_query)
    budget_rows = budget_res.all()

    overall_budget = None
    category_budgets = []

    for b, cat_name in budget_rows:
        limit_amt = float(b.limit_amount)
        if b.scope == "overall" or b.category_id is None:
            overall_budget = limit_amt
        else:
            spent = cat_totals.get(cat_name, 0.0)
            category_budgets.append({
                "category": cat_name or "Category",
                "limit": limit_amt,
                "spent": spent,
                "remaining": max(0.0, limit_amt - spent),
                "is_over": spent > limit_amt,
            })

    # Calculations
    remaining_budget = (overall_budget - total_spent_this_month) if overall_budget else None
    daily_burn = total_spent_this_month / days_elapsed
    safe_daily = (remaining_budget / days_remaining) if (remaining_budget and remaining_budget > 0) else 0.0

    # Recurring charges detection
    recurring_charges = []
    seen_titles: Dict[str, List[float]] = {}
    for e in current_month_expenses + prev_month_expenses:
        t = e["title"].strip().lower()
        if len(t) >= 3:
            seen_titles.setdefault(t, []).append(e["amount"])
    for t, amounts in seen_titles.items():
        if len(amounts) >= 2 and max(amounts) - min(amounts) < 50:
            recurring_charges.append({
                "title": t.title(),
                "monthly_charge": round(sum(amounts) / len(amounts), 2),
            })

    return {
        "current_date": str(now),
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "total_spent_this_month": round(total_spent_this_month, 2),
        "total_spent_prev_month": round(total_spent_prev_month, 2),
        "overall_budget": overall_budget,
        "remaining_overall_budget": round(remaining_budget, 2) if remaining_budget is not None else None,
        "daily_burn_rate": round(daily_burn, 2),
        "safe_daily_spend": round(safe_daily, 2),
        "category_breakdown": {k: round(v, 2) for k, v in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)},
        "category_budgets": category_budgets,
        "largest_expense": largest_expense,
        "recurring_charges": recurring_charges[:5],
        "recent_transactions": current_month_expenses[:10],
    }


def _generate_fallback_answer(
    question: str,
    ctx: Dict[str, Any],
) -> AskAiQueryResponse:
    """
    Intelligent deterministic conversational fallback when LLM is unavailable or rate-limited.
    Matches financial intent from keywords and numbers.
    """
    q_lower = question.lower()
    total_spent = ctx["total_spent_this_month"]
    overall_budget = ctx["overall_budget"]
    remaining = ctx["remaining_overall_budget"]
    safe_daily = ctx["safe_daily_spend"]
    cat_breakdown = ctx["category_breakdown"]
    largest = ctx["largest_expense"]
    recurring = ctx["recurring_charges"]

    suggested_followups = [
        "How much budget do I have left?",
        "Where did most of my money go this month?",
        "What are my recurring subscriptions?",
        "What was my biggest expense?",
    ]

    # Intent 1: Budget / Remaining / Left
    if any(k in q_lower for k in ["budget", "remaining", "left", "limit", "allowance"]):
        if overall_budget:
            status_text = "within your budget" if remaining > 0 else "exceeding your budget"
            overage_text = f"You are currently **{status_text}**."
            answer = (
                f"### 🎯 Monthly Budget Summary\n\n"
                f"- **Total Monthly Budget:** ₹{overall_budget:,.2f}\n"
                f"- **Spent So Far:** ₹{total_spent:,.2f} ({round(total_spent / overall_budget * 100, 1)}%)\n"
                f"- **Remaining Balance:** **₹{max(0.0, remaining):,.2f}**\n"
                f"- **Safe Daily Allowance:** **₹{safe_daily:,.2f}/day** for the remaining {ctx['days_remaining']} days.\n\n"
                f"{overage_text}"
            )
            # Add category budget overages if any
            over_cats = [b for b in ctx["category_budgets"] if b["is_over"]]
            if over_cats:
                cat_lines = "\n".join(f"- **{b['category']}:** Spent ₹{b['spent']:,.0f} (Limit ₹{b['limit']:,.0f})" for b in over_cats)
                answer += f"\n\n⚠️ **Categories over limit:**\n{cat_lines}"
        else:
            answer = (
                f"You have spent **₹{total_spent:,.2f}** this month across {len(ctx['recent_transactions'])} transactions. "
                f"You currently don't have an overall monthly budget limit configured. You can set one on the Dashboard to track remaining limits!"
            )
        return AskAiQueryResponse(
            answer=answer,
            related_metrics={"total_spent": total_spent, "remaining": remaining, "safe_daily_spend": safe_daily},
            suggested_followups=suggested_followups,
            provider="Rule-based Financial Engine",
        )

    # Intent 2: Category spending (e.g. Food, Groceries, Shopping, Travel, Entertainment)
    for cat, amt in cat_breakdown.items():
        if cat.lower() in q_lower or any(word in q_lower for word in cat.lower().split() if len(word) > 2):
            pct = round((amt / total_spent * 100), 1) if total_spent > 0 else 0
            matching_expenses = [e for e in ctx["recent_transactions"] if e["category"].lower() == cat.lower()]
            items_list = "\n".join(f"- {e['title']}: ₹{e['amount']:,.0f} ({e['date']})" for e in matching_expenses[:5])
            answer = (
                f"### 📊 Spending in **{cat}**\n\n"
                f"- **Total Spent This Month:** **₹{amt:,.2f}** ({pct}% of all spending)\n"
                f"- **Recent Transactions:**\n{items_list if items_list else 'No recent items logged.'}\n\n"
                f"💡 *Tip:* You can view and filter all {cat} logs under the Expenses tab."
            )
            return AskAiQueryResponse(
                answer=answer,
                related_metrics={"category": cat, "amount": amt, "percentage": pct},
                suggested_followups=[f"What is my budget for {cat}?", "How much did I spend overall?", "What was my biggest expense?"],
                provider="Rule-based Financial Engine",
            )

    # Intent 3: Can I afford X / Affordability
    if any(k in q_lower for k in ["afford", "can i buy", "should i buy", "can i spend"]):
        # Extract number if present
        nums = re.findall(r"\d[\d,]*", q_lower.replace("₹", "").replace("rs", ""))
        amount_target = None
        if nums:
            try:
                amount_target = float(nums[0].replace(",", ""))
            except Exception:
                amount_target = None

        if amount_target and remaining is not None:
            can_afford = amount_target <= remaining
            new_remaining = remaining - amount_target
            new_safe_daily = max(0.0, new_remaining / ctx["days_remaining"])
            if can_afford:
                answer = (
                    f"### 🛍️ Affordability Analysis for ₹{amount_target:,.2f}\n\n"
                    f"**Yes, you can afford this purchase!**\n\n"
                    f"- Current remaining budget: **₹{remaining:,.2f}**\n"
                    f"- Balance after purchase: **₹{new_remaining:,.2f}**\n"
                    f"- Adjusted safe daily spend: **₹{new_safe_daily:,.2f}/day** for the next {ctx['days_remaining']} days.\n\n"
                    f"💡 *Tip:* Since you still have healthy room in your budget, this purchase will not push you into deficit."
                )
            else:
                answer = (
                    f"### ⚠️ Affordability Warning for ₹{amount_target:,.2f}\n\n"
                    f"**Caution:** Making a ₹{amount_target:,.2f} purchase would exceed your remaining monthly budget.\n\n"
                    f"- Current remaining budget: **₹{remaining:,.2f}**\n"
                    f"- Shortfall / Deficit: **₹{amount_target - remaining:,.2f}**\n\n"
                    f"💡 *Recommendation:* Consider postponing this purchase until next month or reallocating from non-essential categories."
                )
        else:
            answer = (
                f"To check if you can afford a purchase, compare it against your current remaining budget of **₹{remaining:,.2f}**. "
                f"Your safe daily spending limit is currently **₹{safe_daily:,.2f}/day**."
            )
        return AskAiQueryResponse(
            answer=answer,
            related_metrics={"remaining": remaining, "target_amount": amount_target},
            suggested_followups=suggested_followups,
            provider="Rule-based Financial Engine",
        )


    # Intent 4: Biggest / Highest Expense
    if any(k in q_lower for k in ["biggest", "highest", "largest", "max"]):
        if largest:
            notes_line = f"- **Notes:** {largest['notes']}\n" if largest.get("notes") else ""
            answer = (
                f"### 🏆 Largest Transaction This Month\n\n"
                f"- **Item:** **{largest['title']}**\n"
                f"- **Amount:** **₹{largest['amount']:,.2f}**\n"
                f"- **Category:** {largest['category']}\n"
                f"- **Date:** {largest['date']}\n"
                f"- **Payment Mode:** {largest['payment_mode'].upper()}\n"
                f"{notes_line}"
            )
        else:
            answer = "You haven't logged any transactions for this month yet."
        return AskAiQueryResponse(
            answer=answer,
            related_metrics=largest,
            suggested_followups=suggested_followups,
            provider="Rule-based Financial Engine",
        )

    # Intent 5: Subscriptions / Recurring
    if any(k in q_lower for k in ["subscription", "recurring", "netflix", "spotify", "gym", "monthly charge"]):
        if recurring:
            sub_total = sum(r["monthly_charge"] for r in recurring)
            sub_lines = "\n".join(f"- **{r['title']}:** ₹{r['monthly_charge']:,.0f}/month" for r in recurring)
            answer = (
                f"### 🔁 Detected Recurring Subscriptions\n\n"
                f"Identified **{len(recurring)} recurring services** totaling **~₹{sub_total:,.0f} / month**:\n\n"
                f"{sub_lines}\n\n"
                f"💡 *Tip:* Review these services regularly. Canceling unneeded subscriptions is the quickest way to free up monthly savings."
            )
        else:
            answer = "No repeating monthly subscription charges were detected in your recent transaction history."
        return AskAiQueryResponse(
            answer=answer,
            related_metrics={"recurring_total": sum(r["monthly_charge"] for r in recurring) if recurring else 0},
            suggested_followups=suggested_followups,
            provider="Rule-based Financial Engine",
        )

    # Default Intent: General Overview & Breakdown
    top_cats = list(cat_breakdown.items())[:3]
    top_lines = "\n".join(f"- **{c}:** ₹{a:,.0f} ({round(a / total_spent * 100, 1)}%)" for c, a in top_cats) if top_cats else "None"
    answer = (
        f"### 💡 Financial Snapshot (This Month)\n\n"
        f"- **Total Spent:** **₹{total_spent:,.2f}**\n"
        f"- **Daily Burn Rate:** ₹{ctx['daily_burn_rate']:,.2f}/day\n"
        f"- **Remaining Budget:** **₹{remaining:,.2f}** (Safe: ₹{safe_daily:,.2f}/day)\n\n"
        f"**Top Spending Categories:**\n{top_lines}\n\n"
        f"Feel free to ask me questions like: *\"How much did I spend on Food?\"*, *\"What is my remaining budget?\"*, or *\"Can I afford a ₹3,000 dinner?\"*!"
    )
    return AskAiQueryResponse(
        answer=answer,
        related_metrics={"total_spent": total_spent, "remaining": remaining},
        suggested_followups=suggested_followups,
        provider="Rule-based Financial Engine",
    )


async def answer_user_financial_query(
    db: AsyncSession,
    user: User,
    payload: AskAiQueryRequest,
) -> AskAiQueryResponse:
    """
    Answer a user's natural language question about their personal finances.
    Uses Google Gemini if available, with intelligent deterministic fallback.
    """
    # 1. Fetch user financial context
    ctx = await _gather_assistant_financial_context(db, user.id)

    # 2. Check if LLM provider is available
    llm = get_llm_provider()

    if llm and ctx["total_spent_this_month"] > 0:
        system_instruction = (
            "You are FinTrack AI, an intelligent, friendly, and trustworthy personal financial advisor. "
            "You have access to the user's real, isolated financial dataset. "
            "Answer the user's question accurately, concisely, and helpfully based strictly on the provided numbers. "
            "Never invent fictional transactions or numbers. All amounts are in Indian Rupees (₹). "
            "Format your answer with clear markdown (bolding, bullet points, headers). "
            "Return strictly JSON matching: "
            "{'answer': string, 'related_metrics': object, 'suggested_followups': [string, string, string]}."
        )

        history_context = ""
        if payload.history:
            history_context = "\n".join(f"{msg.role.capitalize()}: {msg.content}" for msg in payload.history[-4:])

        prompt = (
            f"User Financial Dataset:\n"
            f"- Current Date: {ctx['current_date']} (Day {ctx['days_elapsed']} of month, {ctx['days_remaining']} days left)\n"
            f"- Total Spent This Month: ₹{ctx['total_spent_this_month']}\n"
            f"- Previous Month Spend: ₹{ctx['total_spent_prev_month']}\n"
            f"- Overall Monthly Budget: ₹{ctx['overall_budget']} (Remaining: ₹{ctx['remaining_overall_budget']})\n"
            f"- Daily Burn Rate: ₹{ctx['daily_burn_rate']}/day\n"
            f"- Safe Daily Spend Allowance: ₹{ctx['safe_daily_spend']}/day\n"
            f"- Category Breakdown: {ctx['category_breakdown']}\n"
            f"- Category Budgets: {ctx['category_budgets']}\n"
            f"- Largest Expense: {ctx['largest_expense']}\n"
            f"- Detected Recurring Charges: {ctx['recurring_charges']}\n"
            f"- Recent 10 Transactions: {ctx['recent_transactions']}\n\n"
            f"{f'Previous Conversation Context:\n{history_context}\n\n' if history_context else ''}"
            f"User Question: \"{payload.question}\"\n\n"
            f"Provide a helpful answer strictly grounded in these numbers."
        )

        try:
            res_json = await llm.generate_structured_json(
                system_instruction=system_instruction,
                prompt=prompt,
            )
            answer_text = res_json.get("answer")
            if answer_text:
                return AskAiQueryResponse(
                    answer=answer_text,
                    related_metrics=res_json.get("related_metrics"),
                    suggested_followups=res_json.get("suggested_followups") or [
                        "How much budget do I have left?",
                        "What is my daily burn rate?",
                        "What was my biggest expense?",
                    ],
                    provider=f"Gemini ({settings.AI_MODEL_NAME})",
                )
        except Exception as exc:
            logger.warning(f"Gemini assistant error: {exc}. Falling back to deterministic engine.")

    # 3. Fallback to deterministic financial engine
    return _generate_fallback_answer(payload.question, ctx)
