from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated wrapper response."""

    items: List[T]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class ErrorDetail(BaseModel):
    """Details about a specific error."""

    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    """Standard centralized API error structure."""

    error: ErrorDetail
