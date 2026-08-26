import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from app.schemas.expense import ExpenseResponse
from app.schemas.budget import BudgetStatusResponse


class DashboardSummaryResponse(BaseModel):
    total_spent: Decimal
    recent_expenses: List[ExpenseResponse]
    budgets_status: List[BudgetStatusResponse]

    class Config:
        from_attributes = True


class CategoryBreakdownItem(BaseModel):
    category_id: Optional[UUID] = None
    category_name: str
    total_spent: Decimal
    percentage: float

    class Config:
        from_attributes = True


class SpendingTrendItem(BaseModel):
    date: Optional[datetime.date] = None
    total_spent: Decimal

    class Config:
        from_attributes = True


class MoMComparisonResponse(BaseModel):
    current_month_spent: Decimal
    previous_month_spent: Decimal
    percentage_change: Optional[float] = None

    class Config:
        from_attributes = True


class TopCategoryItem(BaseModel):
    category_id: Optional[UUID] = None
    category_name: str
    total_spent: Decimal

    class Config:
        from_attributes = True


class AverageSpendResponse(BaseModel):
    average_spent: Decimal
    current_month_spent: Decimal
    basis: str

    class Config:
        from_attributes = True
