"""Monitoring and keyword tracking models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MonitorStatus(str, Enum):
    """Monitor task status enumeration."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class MonitorTask(BaseModel):
    """VK monitoring task model."""

    __tablename__ = "monitor_tasks"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # VK target configuration
    target_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # group, user, post
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Monitoring configuration
    status: Mapped[MonitorStatus] = mapped_column(
        SQLEnum(MonitorStatus), default=MonitorStatus.ACTIVE
    )
    check_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    max_comments_per_check: Mapped[int] = mapped_column(Integer, default=100)

    # Time range settings
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Processing statistics
    total_comments_found: Mapped[int] = mapped_column(BigInteger, default=0)
    total_matches_found: Mapped[int] = mapped_column(BigInteger, default=0)
    last_check_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    keywords: Mapped[List["Keyword"]] = relationship(
        "Keyword", back_populates="monitor_task", cascade="all, delete-orphan"
    )
    matches: Mapped[List["CommentMatch"]] = relationship(
        "CommentMatch", back_populates="monitor_task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MonitorTask(name='{self.name}', target={self.target_type}:{self.target_id})>"


class Keyword(BaseModel):
    """Keyword for comment monitoring."""

    __tablename__ = "keywords"

    monitor_task_id: Mapped[str] = mapped_column(
        ForeignKey("monitor_tasks.id"), nullable=False
    )

    keyword: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    is_regex: Mapped[bool] = mapped_column(Boolean, default=False)
    case_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    weight: Mapped[float] = mapped_column(default=1.0)  # For relevance scoring

    # Statistics
    match_count: Mapped[int] = mapped_column(BigInteger, default=0)
    last_match_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    monitor_task: Mapped["MonitorTask"] = relationship(
        "MonitorTask", back_populates="keywords"
    )
    matches: Mapped[List["CommentMatch"]] = relationship(
        "CommentMatch", back_populates="keyword", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Keyword(keyword='{self.keyword}', matches={self.match_count})>"


class CommentMatch(BaseModel):
    """Match between comment and keyword."""

    __tablename__ = "comment_matches"

    monitor_task_id: Mapped[str] = mapped_column(
        ForeignKey("monitor_tasks.id"), nullable=False
    )
    keyword_id: Mapped[str] = mapped_column(ForeignKey("keywords.id"), nullable=False)
    comment_id: Mapped[str] = mapped_column(
        ForeignKey("vk_comments.id"), nullable=False
    )

    # Match details
    match_text: Mapped[str] = mapped_column(Text, nullable=False)  # Actual matched text
    match_position: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Position in text
    confidence_score: Mapped[float] = mapped_column(default=1.0)

    # Processing flags
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_relevant: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )  # Manual review result
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    monitor_task: Mapped["MonitorTask"] = relationship(
        "MonitorTask", back_populates="matches"
    )
    keyword: Mapped["Keyword"] = relationship("Keyword", back_populates="matches")

    def __repr__(self) -> str:
        return f"<CommentMatch(keyword='{self.keyword.keyword}', match='{self.match_text[:30]}...')>"
