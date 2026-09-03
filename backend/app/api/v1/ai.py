from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, Request

from app.api.deps import current_user_dep, db_dep
from app.config import settings
from app.core.limiter import limiter
from app.schemas.ai import (
    ApplySuggestedBudgetRequest,
    AskAiQueryRequest,
    AskAiQueryResponse,
    FinancialHealthScoreResponse,
    ParsedExpenseDraft,
    PredictiveBudgetResponse,
    QuickAddConfirmRequest,
    QuickAddParseRequest,
    SpendingInsightsResponse,
)
from app.schemas.auth import MessageResponse
from app.schemas.expense import ExpenseResponse
from app.services import (
    ai_assistant_service,
    ai_budget_service,
    ai_health_service,
    ai_insight_service,
    ai_quickadd_service,
)

router = APIRouter(tags=["ai"])


@router.get("/insights", response_model=SpendingInsightsResponse)
async def get_insights(
    db: db_dep,
    current_user: current_user_dep,
) -> SpendingInsightsResponse:
    """
    Retrieve personalized AI financial insights and cost-saving opportunities
    strictly isolated to the authenticated user.
    """
    return await ai_insight_service.get_user_spending_insights(
        db, current_user, force_refresh=False
    )


@router.post("/insights/refresh", response_model=SpendingInsightsResponse)
@limiter.limit(settings.AI_RATE_LIMIT)
async def refresh_insights(
    request: Request,
    db: db_dep,
    current_user: current_user_dep,
) -> SpendingInsightsResponse:
    """
    Force-regenerate fresh AI financial insights and cost-saving suggestions.
    Rate-limited to prevent abuse.
    """
    return await ai_insight_service.get_user_spending_insights(
        db, current_user, force_refresh=True
    )


@router.get("/predictive-budget", response_model=PredictiveBudgetResponse)
async def get_predictive_budget(
    db: db_dep,
    current_user: current_user_dep,
) -> PredictiveBudgetResponse:
    """
    Retrieve real-time spending velocity forecast, days-to-exhaustion prediction,
    safe daily spend limit, and smart AI budget allocations.
    """
    return await ai_budget_service.get_predictive_budget_forecast(db, current_user)


@router.post("/predictive-budget/apply", response_model=MessageResponse)
async def apply_recommended_budget(
    payload: ApplySuggestedBudgetRequest,
    db: db_dep,
    current_user: current_user_dep,
) -> MessageResponse:
    """
    1-click apply an AI-suggested budget limit to a category for the current month.
    """
    budget = await ai_budget_service.apply_suggested_budget(
        db,
        user=current_user,
        category_id=UUID(payload.category_id),
        amount=payload.amount,
    )
    return MessageResponse(
        message=f"Successfully set budget limit to ₹{budget.limit_amount:,.0f} for this category.",
        success=True,
    )


@router.post("/ask", response_model=AskAiQueryResponse)
@limiter.limit(settings.AI_RATE_LIMIT)
async def ask_financial_assistant(
    request: Request,
    payload: AskAiQueryRequest,
    db: db_dep,
    current_user: current_user_dep,
) -> AskAiQueryResponse:
    """
    Interactive conversational financial assistant. Answer user queries about
    their spending, budgets, savings, affordability, and trends strictly based
    on their isolated personal financial records.
    """
    return await ai_assistant_service.answer_user_financial_query(
        db,
        user=current_user,
        payload=payload,
    )


@router.post("/quick-add/parse", response_model=ParsedExpenseDraft)
@limiter.limit(settings.AI_RATE_LIMIT)
async def parse_quick_add(
    request: Request,
    payload: QuickAddParseRequest,
    db: db_dep,
    current_user: current_user_dep,
) -> ParsedExpenseDraft:
    """
    Parse a free-form natural language expense string into a structured draft
    with auto-categorization and date/amount parsing.
    """
    return await ai_quickadd_service.parse_natural_language_expense(
        db,
        user=current_user,
        text=payload.text,
    )


@router.post("/quick-add/confirm", response_model=ExpenseResponse)
async def confirm_quick_add(
    payload: QuickAddConfirmRequest,
    db: db_dep,
    current_user: current_user_dep,
) -> ExpenseResponse:
    """
    Save the confirmed parsed expense directly to the database.
    """
    return await ai_quickadd_service.confirm_and_save_expense(
        db,
        user=current_user,
        payload=payload,
    )


@router.get("/health-score", response_model=FinancialHealthScoreResponse)
async def get_financial_health_score(
    db: db_dep,
    current_user: current_user_dep,
) -> FinancialHealthScoreResponse:
    """
    Calculate 0-100 monthly financial health score and executive digest
    across budget adherence, savings velocity, and category discipline.
    """
    return await ai_health_service.calculate_monthly_financial_health(
        db,
        user=current_user,
    )
