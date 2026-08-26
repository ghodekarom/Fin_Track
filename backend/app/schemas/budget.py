import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.category import CategoryBriefResponse


class BudgetBase(BaseModel):
    scope: Literal["overall", "category"]
    category_id: uuid.UUID | None = None
    period_month: date
    limit_amount: Decimal = Field(..., gt=0)

    @field_validator("period_month")
    @classmethod
    def force_first_day_of_month(cls, v: date) -> date:
        return date(v.year, v.month, 1)

    @model_validator(mode="after")
    def validate_scope_category_relation(cls, values: "BudgetBase") -> "BudgetBase":
        if values.scope == "overall" and values.category_id is not None:
            raise ValueError("Overall budget scope must not have a category_id")
        if values.scope == "category" and values.category_id is None:
            raise ValueError("Category budget scope must have a category_id")
        return values


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    limit_amount: Decimal = Field(..., gt=0)


class BudgetResponse(BaseModel):
    id: uuid.UUID
    scope: str
    category_id: uuid.UUID | None
    category: CategoryBriefResponse | None = None
    period_month: date
    limit_amount: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetStatusResponse(BaseModel):
    id: uuid.UUID
    scope: str
    category_id: uuid.UUID | None
    category_name: str | None = None
    period_month: date
    limit_amount: Decimal
    spent: Decimal
    remaining: Decimal
    status: Literal["on_track", "near_limit", "over_budget"]

    class Config:
        from_attributes = True
