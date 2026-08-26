from datetime import date
from typing import Literal
from fastapi import APIRouter, Query

from app.api.deps import db_dep
from app.services import dashboard_service
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    CategoryBreakdownItem,
    SpendingTrendItem,
    MoMComparisonResponse,
    TopCategoryItem,
    AverageSpendResponse,
)

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    db: db_dep,
    period_month: date | None = Query(
        None, description="Month of the summary (defaults to current month)"
    ),
) -> DashboardSummaryResponse:
    """Retrieve total spent, recent expenses, and budget warnings for the dashboard."""
    if period_month is None:
        period_month = date.today()
    return await dashboard_service.get_summary(db, period_month)


@router.get("/charts/category-breakdown", response_model=list[CategoryBreakdownItem])
async def get_category_breakdown(
    db: db_dep,
    date_from: date | None = Query(None, description="Filter start date"),
    date_to: date | None = Query(None, description="Filter end date"),
) -> list[CategoryBreakdownItem]:
    """Retrieve category-wise spending data suitable for pie/donut charts."""
    return await dashboard_service.get_category_breakdown(db, date_from, date_to)


@router.get("/charts/spending-trend", response_model=list[SpendingTrendItem])
async def get_spending_trend(
    db: db_dep,
    period: Literal["daily", "weekly", "monthly"] = Query(
        "daily", description="Time interval grouping basis"
    ),
    date_from: date | None = Query(None, description="Filter start date"),
    date_to: date | None = Query(None, description="Filter end date"),
) -> list[SpendingTrendItem]:
    """Retrieve spending data points mapped over time (daily, weekly, monthly intervals)."""
    return await dashboard_service.get_spending_trend(
        db, period, date_from, date_to
    )


@router.get("/reports", response_model=list[SpendingTrendItem])
async def get_reports_breakdown(
    db: db_dep,
    period: Literal["daily", "weekly", "monthly"] = Query(
        "monthly", description="Report interval basis"
    ),
) -> list[SpendingTrendItem]:
    """Retrieve periodic breakdown reports of spending."""
    # This matches spending trend but defaults to full history / standard ranges
    return await dashboard_service.get_spending_trend(db, period)


@router.get("/comparison", response_model=MoMComparisonResponse)
async def get_mom_comparison(db: db_dep) -> MoMComparisonResponse:
    """Retrieve month-over-month total spending comparison and percentage change."""
    return await dashboard_service.get_comparison(db)


@router.get("/top-categories", response_model=list[TopCategoryItem])
async def get_top_categories(
    db: db_dep,
    limit: int = Query(5, ge=1, description="Number of top categories to return"),
) -> list[TopCategoryItem]:
    """Retrieve top categories sorted by spending."""
    return await dashboard_service.get_top_categories(db, limit)


@router.get("/average-spend", response_model=AverageSpendResponse)
async def get_average_spend(
    db: db_dep,
    basis: Literal["daily", "weekly"] = Query(
        "daily", description="Average frequency basis"
    ),
) -> AverageSpendResponse:
    """Retrieve average daily/weekly spending rate in the current month."""
    return await dashboard_service.get_average_spend(db, basis)
