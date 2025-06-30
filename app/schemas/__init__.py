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
    "CommentMatchCreate",
    "CommentMatchResponse",
    "KeywordCreate",
    "KeywordResponse",
    # Monitoring schemas
    "MonitorTaskCreate",
    "MonitorTaskResponse",
    "MonitorTaskUpdate",
    "VKCommentCreate",
    "VKCommentResponse",
    "VKPostCreate",
    "VKPostResponse",
    # VK schemas
    "VKUserCreate",
    "VKUserResponse",
]
