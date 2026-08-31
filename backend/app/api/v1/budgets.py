import uuid
from datetime import date
from fastapi import APIRouter, Query, status

from app.api.deps import current_user_dep, db_dep
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetStatusResponse, BudgetUpdate
from app.services import budget_service

router = APIRouter()


@router.get("", response_model=list[BudgetResponse])
async def list_budgets(
    db: db_dep,
    current_user: current_user_dep,
    period_month: date | None = Query(
        None, description="Month of the budgets (YYYY-MM-DD)"
    ),
) -> list[BudgetResponse]:
    """List budgets configured for authenticated user."""
    return await budget_service.get_budgets(db, current_user.id, period_month)


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    db: db_dep,
    current_user: current_user_dep,
    payload: BudgetCreate,
) -> BudgetResponse:
    """Create a new budget goal (overall or per-category) for authenticated user."""
    return await budget_service.create_budget(db, current_user.id, payload)


@router.get("/status", response_model=list[BudgetStatusResponse])
async def get_budgets_status(
    db: db_dep,
    current_user: current_user_dep,
    period_month: date | None = Query(
        None, description="Month for checking status (defaults to current month)"
    ),
) -> list[BudgetStatusResponse]:
    """Retrieve live warning status, spent, and remaining balance for authenticated user's budgets."""
    if period_month is None:
        period_month = date.today()
    return await budget_service.get_budgets_status(db, current_user.id, period_month)


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    db: db_dep,
    current_user: current_user_dep,
    budget_id: uuid.UUID,
) -> BudgetResponse:
    """Get details of a single user-owned budget goal."""
    return await budget_service.get_budget_by_id(db, current_user.id, budget_id)


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    db: db_dep,
    current_user: current_user_dep,
    budget_id: uuid.UUID,
    payload: BudgetUpdate,
) -> BudgetResponse:
    """Update limit amount of a user-owned budget goal."""
    return await budget_service.update_budget(db, current_user.id, budget_id, payload)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    db: db_dep,
    current_user: current_user_dep,
    budget_id: uuid.UUID,
) -> None:
    """Remove a user-owned budget goal."""
    await budget_service.delete_budget(db, current_user.id, budget_id)
