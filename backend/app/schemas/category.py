import uuid
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=50)

    @field_validator("name")
    @classmethod
    def validate_and_strip_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Category name cannot be empty or whitespace only")
        return stripped


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryBriefResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    expense_count: int = 0

    class Config:
        from_attributes = True
        json_encoders = {uuid.UUID: lambda x: str(x)}
