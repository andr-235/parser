"""Pydantic schemas for VK models."""

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseResponseSchema, BaseSchema


# VK User Schemas
class VKUserBase(BaseSchema):
    """Base VK User schema."""

    vk_id: int = Field(..., description="VK user ID")
    first_name: str = Field(..., max_length=100, description="First name")
    last_name: str = Field(..., max_length=100, description="Last name")
    screen_name: str | None = Field(None, max_length=100, description="Screen name")
    photo_50: str | None = Field(None, max_length=255, description="Photo 50px")
    photo_100: str | None = Field(None, max_length=255, description="Photo 100px")
    is_closed: bool = Field(False, description="Is profile closed")
    can_access_closed: bool = Field(False, description="Can access closed profile")
    is_deactivated: bool = Field(False, description="Is profile deactivated")


class VKUserCreate(VKUserBase):
    """VK User creation schema."""


class VKUserResponse(VKUserBase, BaseResponseSchema):
    """VK User response schema."""

    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}"


# VK Post Schemas
class VKPostBase(BaseSchema):
    """Base VK Post schema."""

    vk_id: int = Field(..., description="VK post ID")
    owner_id: int = Field(..., description="Post owner ID")
    from_id: int = Field(..., description="Post author ID")
    text: str | None = Field(None, description="Post text")
    post_type: str = Field("post", max_length=20, description="Post type")
    is_pinned: bool = Field(False, description="Is post pinned")
    marked_as_ads: bool = Field(False, description="Is marked as ads")
    published_at: datetime = Field(..., description="Publication timestamp")
    likes_count: int = Field(0, ge=0, description="Number of likes")
    reposts_count: int = Field(0, ge=0, description="Number of reposts")
    comments_count: int = Field(0, ge=0, description="Number of comments")
    views_count: int | None = Field(None, ge=0, description="Number of views")


class VKPostCreate(VKPostBase):
    """VK Post creation schema."""


class VKPostResponse(VKPostBase, BaseResponseSchema):
    """VK Post response schema."""


# VK Comment Schemas
class VKCommentBase(BaseSchema):
    """Base VK Comment schema."""

    vk_id: int = Field(..., description="VK comment ID")
    post_id: int = Field(..., description="Post ID")
    from_id: int = Field(..., description="Author ID")
    text: str = Field(..., min_length=1, description="Comment text")
    published_at: datetime = Field(..., description="Publication timestamp")
    reply_to_user: int | None = Field(None, description="Reply to user ID")
    reply_to_comment: int | None = Field(None, description="Reply to comment ID")
    likes_count: int = Field(0, ge=0, description="Number of likes")
    is_processed: bool = Field(False, description="Is comment processed")
    contains_keywords: bool = Field(False, description="Contains monitored keywords")
    sentiment_score: float | None = Field(
        None, ge=-1.0, le=1.0, description="Sentiment analysis score"
    )


class VKCommentCreate(VKCommentBase):
    """VK Comment creation schema."""


class VKCommentResponse(VKCommentBase, BaseResponseSchema):
    """VK Comment response schema."""


class VKCommentWithAuthor(VKCommentResponse):
    """VK Comment with author information."""

    author: VKUserResponse = Field(..., description="Comment author")


class VKCommentWithPost(VKCommentResponse):
    """VK Comment with post information."""

    post: VKPostResponse = Field(..., description="Related post")
