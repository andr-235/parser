"""Pydantic schemas for monitoring models."""

from datetime import datetime

from pydantic import Field

from app.models.monitoring import MonitorStatus
from app.schemas.base import BaseResponseSchema, BaseSchema


# Monitor Task Schemas
class MonitorTaskBase(BaseSchema):
    """Base Monitor Task schema."""

    name: str = Field(..., max_length=200, description="Task name")
    description: str | None = Field(None, description="Task description")
    target_type: str = Field(
        ..., max_length=20, description="Target type (group, user, post)"
    )
    target_id: int = Field(..., description="VK target ID")
    check_interval_minutes: int = Field(
        15, ge=1, le=1440, description="Check interval in minutes"
    )
    max_comments_per_check: int = Field(
        100, ge=1, le=1000, description="Max comments per check"
    )
    start_date: datetime | None = Field(None, description="Start monitoring date")
    end_date: datetime | None = Field(None, description="End monitoring date")


class MonitorTaskCreate(MonitorTaskBase):
    """Monitor Task creation schema."""

    keywords: list[str] = Field(
        ..., min_length=1, description="List of keywords to monitor"
    )


class MonitorTaskUpdate(BaseSchema):
    """Monitor Task update schema."""

    name: str | None = Field(None, max_length=200, description="Task name")
    description: str | None = Field(None, description="Task description")
    status: MonitorStatus | None = Field(None, description="Task status")
    check_interval_minutes: int | None = Field(
        None, ge=1, le=1440, description="Check interval in minutes"
    )
    max_comments_per_check: int | None = Field(
        None, ge=1, le=1000, description="Max comments per check"
    )
    start_date: datetime | None = Field(None, description="Start monitoring date")
    end_date: datetime | None = Field(None, description="End monitoring date")


class MonitorTaskResponse(MonitorTaskBase, BaseResponseSchema):
    """Monitor Task response schema."""

    status: MonitorStatus = Field(..., description="Task status")
    total_comments_found: int = Field(0, description="Total comments found")
    total_matches_found: int = Field(0, description="Total matches found")
    last_check_at: datetime | None = Field(None, description="Last check timestamp")
    last_error: str | None = Field(None, description="Last error message")


# Keyword Schemas
class KeywordBase(BaseSchema):
    """Base Keyword schema."""

    keyword: str = Field(..., max_length=200, description="Keyword text")
    is_regex: bool = Field(False, description="Is keyword a regex pattern")
    case_sensitive: bool = Field(False, description="Is keyword case sensitive")
    weight: float = Field(1.0, ge=0.1, le=10.0, description="Keyword weight")


class KeywordCreate(KeywordBase):
    """Keyword creation schema."""


class KeywordResponse(KeywordBase, BaseResponseSchema):
    """Keyword response schema."""

    monitor_task_id: str = Field(..., description="Monitor task ID")
    match_count: int = Field(0, description="Number of matches")
    last_match_at: datetime | None = Field(None, description="Last match timestamp")


# Comment Match Schemas
class CommentMatchBase(BaseSchema):
    """Base Comment Match schema."""

    match_text: str = Field(..., description="Matched text")
    match_position: int = Field(..., ge=0, description="Position in text")
    confidence_score: float = Field(
        1.0, ge=0.0, le=1.0, description="Match confidence score"
    )
    is_reviewed: bool = Field(False, description="Is match reviewed")
    is_relevant: bool | None = Field(None, description="Is match relevant")
    notes: str | None = Field(None, description="Review notes")


class CommentMatchCreate(CommentMatchBase):
    """Comment Match creation schema."""

    monitor_task_id: str = Field(..., description="Monitor task ID")
    keyword_id: str = Field(..., description="Keyword ID")
    comment_id: str = Field(..., description="Comment ID")


class CommentMatchResponse(CommentMatchBase, BaseResponseSchema):
    """Comment Match response schema."""

    monitor_task_id: str = Field(..., description="Monitor task ID")
    keyword_id: str = Field(..., description="Keyword ID")
    comment_id: str = Field(..., description="Comment ID")


class MonitorTaskWithKeywords(MonitorTaskResponse):
    """Monitor Task with keywords."""

    keywords: list[KeywordResponse] = Field(..., description="Task keywords")


class CommentMatchWithDetails(CommentMatchResponse):
    """Comment Match with keyword and comment details."""

    keyword: KeywordResponse = Field(..., description="Matched keyword")
