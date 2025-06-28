"""Base Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base Pydantic schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class UUIDSchema(BaseSchema):
    """Schema with UUID id field."""

    id: uuid.UUID


class BaseResponseSchema(UUIDSchema, TimestampSchema):
    """Base response schema with ID and timestamps."""

    pass


class PaginationSchema(BaseSchema):
    """Pagination parameters schema."""

    page: int = 1
    size: int = 50

    @property
    def offset(self) -> int:
        """Calculate offset from page and size."""
        return (self.page - 1) * self.size


class PaginatedResponseSchema(BaseSchema):
    """Paginated response schema."""

    items: list[Dict[str, Any]]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(
        cls,
        items: list[Dict[str, Any]],
        total: int,
        page: int,
        size: int,
    ) -> "PaginatedResponseSchema":
        """Create paginated response."""
        pages = (total + size - 1) // size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )
