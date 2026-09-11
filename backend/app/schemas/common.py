"""Common schema definitions and generics."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standardized error response body."""
    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class PaginationParams(BaseModel):
    """Common pagination query parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    size: int = Field(default=50, ge=1, le=200, description="Items per page")
