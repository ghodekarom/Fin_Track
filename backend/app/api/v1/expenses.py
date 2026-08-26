import uuid
from datetime import date
from decimal import Decimal
from typing import Literal
from fastapi import APIRouter, Query, status

from app.api.deps import db_dep, pagination_dep
from app.schemas.common import PaginatedResponse
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from app.services import expense_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ExpenseResponse])
async def list_expenses(
    db: db_dep,
    pagination: pagination_dep,
    search: str | None = Query(None, description="Search by title or notes"),
    category_id: uuid.UUID | None = Query(None, description="Filter by category ID"),
    date_from: date | None = Query(None, description="Filter from date (inclusive)"),
    date_to: date | None = Query(None, description="Filter to date (inclusive)"),
    amount_min: Decimal | None = Query(None, description="Filter min amount"),
    amount_max: Decimal | None = Query(None, description="Filter max amount"),
    payment_mode: Literal["cash", "card", "upi", "other"] | None = Query(
        None, description="Filter by payment mode"
    ),
    sort_by: Literal["amount", "date", "category"] = Query(
        "date", description="Sort field"
    ),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
) -> PaginatedResponse[ExpenseResponse]:
    """Retrieve filtered, sorted, and paginated expenses list."""
    filters = {
        "search": search,
        "category_id": category_id,
        "date_from": date_from,
        "date_to": date_to,
        "amount_min": amount_min,
        "amount_max": amount_max,
        "payment_mode": payment_mode,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
    result = await expense_service.get_expenses(db, filters, pagination)
    return PaginatedResponse[ExpenseResponse](**result)


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(db: db_dep, payload: ExpenseCreate) -> ExpenseResponse:
    """Log a new expense entry."""
    return await expense_service.create_expense(db, payload)


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(db: db_dep, expense_id: uuid.UUID) -> ExpenseResponse:
    """Get details of a single expense entry."""
    return await expense_service.get_expense_by_id(db, expense_id)


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    db: db_dep, expense_id: uuid.UUID, payload: ExpenseUpdate
) -> ExpenseResponse:
    """Update details of an existing expense."""
    return await expense_service.update_expense(db, expense_id, payload)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(db: db_dep, expense_id: uuid.UUID) -> None:
    """Delete an expense entry."""
    await expense_service.delete_expense(db, expense_id)
