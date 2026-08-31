import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.category import CategoryBriefResponse


class ExpenseBase(BaseModel):
    title: str = Field(..., max_length=50)
    category_id: uuid.UUID
    amount: Decimal = Field(..., gt=0)
    expense_date: date
    notes: str | None = Field(None, max_length=250)
    payment_mode: Literal["cash", "card", "upi", "other"] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or whitespace only")
        return stripped

    @field_validator("expense_date")
    @classmethod
    def validate_date(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date cannot be in the future")
        return v


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    title: str | None = Field(None, max_length=50)
    category_id: uuid.UUID | None = None
    amount: Decimal | None = Field(None, gt=0)
    expense_date: date | None = None
    notes: str | None = Field(None, max_length=250)
    payment_mode: Literal["cash", "card", "upi", "other"] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or whitespace only")
        return stripped

    @field_validator("expense_date")
    @classmethod
    def validate_date(cls, v: date | None) -> date | None:
        if v is None:
            return v
        if v > date.today():
            raise ValueError("Date cannot be in the future")
        return v


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    amount: Decimal
    expense_date: date
    notes: str | None
    payment_mode: str | None
    category_id: uuid.UUID
    category: CategoryBriefResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
