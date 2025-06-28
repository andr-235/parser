"""VK-related database models."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class VKUser(BaseModel):
    """VK User model."""

    __tablename__ = "vk_users"

    vk_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    screen_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    photo_50: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    photo_100: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    can_access_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deactivated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    posts: Mapped[List["VKPost"]] = relationship(
        "VKPost", back_populates="author", cascade="all, delete-orphan"
    )
    comments: Mapped[List["VKComment"]] = relationship(
        "VKComment", back_populates="author", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<VKUser(vk_id={self.vk_id}, name='{self.first_name} {self.last_name}')>"
        )


class VKPost(BaseModel):
    """VK Post model."""

    __tablename__ = "vk_posts"

    vk_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vk_users.vk_id"), nullable=False
    )
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    post_type: Mapped[str] = mapped_column(String(20), default="post")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    marked_as_ads: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # VK engagement metrics
    likes_count: Mapped[int] = mapped_column(BigInteger, default=0)
    reposts_count: Mapped[int] = mapped_column(BigInteger, default=0)
    comments_count: Mapped[int] = mapped_column(BigInteger, default=0)
    views_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Relationships
    author: Mapped["VKUser"] = relationship("VKUser", back_populates="posts")
    comments: Mapped[List["VKComment"]] = relationship(
        "VKComment", back_populates="post", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<VKPost(vk_id={self.vk_id}, owner_id={self.owner_id})>"


class VKComment(BaseModel):
    """VK Comment model."""

    __tablename__ = "vk_comments"

    vk_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vk_posts.vk_id"), nullable=False
    )
    from_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vk_users.vk_id"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # VK comment metadata
    reply_to_user: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reply_to_comment: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Engagement metrics
    likes_count: Mapped[int] = mapped_column(BigInteger, default=0)

    # Processing flags
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_keywords: Mapped[bool] = mapped_column(Boolean, default=False)
    sentiment_score: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Relationships
    post: Mapped["VKPost"] = relationship("VKPost", back_populates="comments")
    author: Mapped["VKUser"] = relationship("VKUser", back_populates="comments")

    def __repr__(self) -> str:
        return f"<VKComment(vk_id={self.vk_id}, post_id={self.post_id}, text='{self.text[:50]}...')>"
