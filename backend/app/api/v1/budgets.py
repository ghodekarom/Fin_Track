import uuid
from datetime import date
from fastapi import APIRouter, Query, status

from app.api.deps import db_dep
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetStatusResponse, BudgetUpdate
from app.services import budget_service

router = APIRouter()


@router.get("", response_model=list[BudgetResponse])
async def list_budgets(
    db: db_dep,
    period_month: date | None = Query(
        None, description="Month of the budgets (YYYY-MM-DD)"
    ),
) -> list[BudgetResponse]:
    """List budgets configured for a specific period."""
    return await budget_service.get_budgets(db, period_month)


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(db: db_dep, payload: BudgetCreate) -> BudgetResponse:
    """Create a new budget goal (overall or per-category)."""
    return await budget_service.create_budget(db, payload)


@router.get("/status", response_model=list[BudgetStatusResponse])
async def get_budgets_status(
    db: db_dep,
    period_month: date | None = Query(
        None, description="Month for checking status (defaults to current month)"
    ),
) -> list[BudgetStatusResponse]:
    """Retrieve live warning status, spent, and remaining balance for all budgets in a month."""
    if period_month is None:
        period_month = date.today()
    return await budget_service.get_budgets_status(db, period_month)


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(db: db_dep, budget_id: uuid.UUID) -> BudgetResponse:
    """Get details of a single budget goal."""
    return await budget_service.get_budget_by_id(db, budget_id)


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    db: db_dep, budget_id: uuid.UUID, payload: BudgetUpdate
) -> BudgetResponse:
    """Update limit amount of a budget goal."""
    return await budget_service.update_budget(db, budget_id, payload)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(db: db_dep, budget_id: uuid.UUID) -> None:
    """Remove a budget goal."""
    await budget_service.delete_budget(db, budget_id)
DarkTheme = True
