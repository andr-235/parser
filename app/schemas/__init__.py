"""Pydantic schemas for VK Comments Monitor API."""

from app.schemas.monitoring import (
    CommentMatchCreate,
    CommentMatchResponse,
    KeywordCreate,
    KeywordResponse,
    MonitorTaskCreate,
    MonitorTaskResponse,
    MonitorTaskUpdate,
)
from app.schemas.vk import (
    VKCommentCreate,
    VKCommentResponse,
    VKPostCreate,
    VKPostResponse,
    VKUserCreate,
    VKUserResponse,
)

__all__ = [
    # VK schemas
    "VKUserCreate",
    "VKUserResponse",
    "VKPostCreate",
    "VKPostResponse",
    "VKCommentCreate",
    "VKCommentResponse",
    # Monitoring schemas
    "MonitorTaskCreate",
    "MonitorTaskUpdate",
    "MonitorTaskResponse",
    "KeywordCreate",
    "KeywordResponse",
    "CommentMatchCreate",
    "CommentMatchResponse",
]
