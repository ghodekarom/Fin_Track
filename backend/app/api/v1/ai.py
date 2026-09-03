from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, Request

from app.api.deps import current_user_dep, db_dep
from app.config import settings
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.ai import (
    ApplySuggestedBudgetRequest,
    PredictiveBudgetResponse,
    SpendingInsightsResponse,
)
from app.schemas.auth import MessageResponse
from app.services import ai_budget_service, ai_insight_service

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
