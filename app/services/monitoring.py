"""Monitoring service for managing monitoring tasks and keyword tracking."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.monitoring import CommentMatch, Keyword, MonitorStatus, MonitorTask
from app.schemas.monitoring import KeywordCreate, MonitorTaskCreate, MonitorTaskUpdate


class MonitoringService:
    """Service for managing monitoring tasks and keyword tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Monitor Task methods
    async def get_task_by_id(self, task_id: uuid.UUID) -> MonitorTask | None:
        """Get monitoring task by ID."""
        result = await self.db.execute(
            select(MonitorTask)
            .options(selectinload(MonitorTask.keywords))
            .where(MonitorTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_tasks_paginated(
        self,
        offset: int = 0,
        limit: int = 50,
        status: MonitorStatus | None = None,
        target_type: str | None = None,
    ) -> tuple[list[MonitorTask], int]:
        """Get paginated list of monitoring tasks."""
        query = select(MonitorTask).options(selectinload(MonitorTask.keywords))
        count_query = select(func.count(MonitorTask.id))

        # Apply filters
        if status:
            query = query.where(MonitorTask.status == status)
            count_query = count_query.where(MonitorTask.status == status)

        if target_type:
            query = query.where(MonitorTask.target_type == target_type)
            count_query = count_query.where(MonitorTask.target_type == target_type)

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get tasks
        result = await self.db.execute(
            query.offset(offset).limit(limit).order_by(MonitorTask.created_at.desc())
        )
        tasks = result.scalars().all()

        return list(tasks), total

    async def create_task(self, task_data: MonitorTaskCreate) -> MonitorTask:
        """Create new monitoring task with keywords."""
        # Create task
        task_dict = task_data.model_dump(exclude={"keywords"})
        task = MonitorTask(**task_dict)
        self.db.add(task)
        await self.db.flush()  # Get the task ID

        # Create keywords
        for keyword_text in task_data.keywords:
            keyword = Keyword(
                monitor_task_id=task.id,
                keyword=keyword_text,
                is_regex=False,
                case_sensitive=False,
                weight=1.0,
            )
            self.db.add(keyword)

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_task(
        self, task_id: uuid.UUID, task_update: MonitorTaskUpdate
    ) -> MonitorTask | None:
        """Update monitoring task."""
        task = await self.get_task_by_id(task_id)
        if not task:
            return None

        update_data = task_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(task, field):
                setattr(task, field, value)

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: uuid.UUID) -> bool:
        """Delete monitoring task."""
        task = await self.get_task_by_id(task_id)
        if not task:
            return False

        await self.db.delete(task)
        await self.db.commit()
        return True

    async def start_task(self, task_id: uuid.UUID) -> MonitorTask | None:
        """Start monitoring task."""
        return await self._update_task_status(task_id, MonitorStatus.ACTIVE)

    async def pause_task(self, task_id: uuid.UUID) -> MonitorTask | None:
        """Pause monitoring task."""
        return await self._update_task_status(task_id, MonitorStatus.PAUSED)

    async def complete_task(self, task_id: uuid.UUID) -> MonitorTask | None:
        """Complete monitoring task."""
        return await self._update_task_status(task_id, MonitorStatus.COMPLETED)

    async def error_task(
        self, task_id: uuid.UUID, error_message: str
    ) -> MonitorTask | None:
        """Mark task as error with message."""
        task = await self.get_task_by_id(task_id)
        if not task:
            return None

        task.status = MonitorStatus.ERROR
        task.last_error = error_message
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def _update_task_status(
        self, task_id: uuid.UUID, status: MonitorStatus
    ) -> MonitorTask | None:
        """Update task status."""
        task = await self.get_task_by_id(task_id)
        if not task:
            return None

        task.status = status
        if status == MonitorStatus.ACTIVE:
            task.last_error = None  # Clear error when starting
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_task_stats(
        self,
        task_id: uuid.UUID,
        comments_found: int = 0,
        matches_found: int = 0,
    ) -> MonitorTask | None:
        """Update task statistics."""
        task = await self.get_task_by_id(task_id)
        if not task:
            return None

        task.total_comments_found += comments_found
        task.total_matches_found += matches_found
        task.last_check_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(task)
        return task

    # Keyword methods
    async def get_keyword_by_id(self, keyword_id: uuid.UUID) -> Keyword | None:
        """Get keyword by ID."""
        result = await self.db.execute(select(Keyword).where(Keyword.id == keyword_id))
        return result.scalar_one_or_none()

    async def get_task_keywords(self, task_id: uuid.UUID) -> list[Keyword]:
        """Get all keywords for a task."""
        result = await self.db.execute(
            select(Keyword)
            .where(Keyword.monitor_task_id == task_id)
            .order_by(Keyword.created_at.asc())
        )
        return list(result.scalars().all())

    async def add_keyword(
        self, task_id: uuid.UUID, keyword_data: KeywordCreate
    ) -> Keyword:
        """Add keyword to monitoring task."""
        keyword = Keyword(monitor_task_id=task_id, **keyword_data.model_dump())
        self.db.add(keyword)
        await self.db.commit()
        await self.db.refresh(keyword)
        return keyword

    async def delete_keyword(self, keyword_id: uuid.UUID) -> bool:
        """Delete keyword."""
        keyword = await self.get_keyword_by_id(keyword_id)
        if not keyword:
            return False

        await self.db.delete(keyword)
        await self.db.commit()
        return True

    async def update_keyword_stats(
        self, keyword_id: uuid.UUID, new_match: bool = True
    ) -> Keyword | None:
        """Update keyword match statistics."""
        keyword = await self.get_keyword_by_id(keyword_id)
        if not keyword:
            return None

        if new_match:
            keyword.match_count += 1
            keyword.last_match_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(keyword)
        return keyword

    # Comment Match methods
    async def get_match_by_id(self, match_id: uuid.UUID) -> CommentMatch | None:
        """Get comment match by ID."""
        result = await self.db.execute(
            select(CommentMatch)
            .options(selectinload(CommentMatch.keyword))
            .where(CommentMatch.id == match_id)
        )
        return result.scalar_one_or_none()

    async def get_matches_paginated(
        self,
        offset: int = 0,
        limit: int = 50,
        task_id: uuid.UUID | None = None,
        is_reviewed: bool | None = None,
        is_relevant: bool | None = None,
    ) -> tuple[list[CommentMatch], int]:
        """Get paginated list of comment matches."""
        query = select(CommentMatch).options(
            selectinload(CommentMatch.keyword), selectinload(CommentMatch.monitor_task)
        )
        count_query = select(func.count(CommentMatch.id))

        # Apply filters
        if task_id:
            query = query.where(CommentMatch.monitor_task_id == task_id)
            count_query = count_query.where(CommentMatch.monitor_task_id == task_id)

        if is_reviewed is not None:
            query = query.where(CommentMatch.is_reviewed == is_reviewed)
            count_query = count_query.where(CommentMatch.is_reviewed == is_reviewed)

        if is_relevant is not None:
            query = query.where(CommentMatch.is_relevant == is_relevant)
            count_query = count_query.where(CommentMatch.is_relevant == is_relevant)

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get matches
        result = await self.db.execute(
            query.offset(offset).limit(limit).order_by(CommentMatch.created_at.desc())
        )
        matches = result.scalars().all()

        return list(matches), total

    async def create_match(
        self,
        monitor_task_id: uuid.UUID,
        keyword_id: uuid.UUID,
        comment_id: uuid.UUID,
        match_text: str,
        match_position: int,
        confidence_score: float = 1.0,
    ) -> CommentMatch:
        """Create new comment match."""
        match = CommentMatch(
            monitor_task_id=monitor_task_id,
            keyword_id=keyword_id,
            comment_id=comment_id,
            match_text=match_text,
            match_position=match_position,
            confidence_score=confidence_score,
        )
        self.db.add(match)
        await self.db.commit()
        await self.db.refresh(match)
        return match

    async def review_match(
        self,
        match_id: uuid.UUID,
        is_relevant: bool,
        notes: str | None = None,
    ) -> CommentMatch | None:
        """Review comment match."""
        match = await self.get_match_by_id(match_id)
        if not match:
            return None

        match.is_reviewed = True
        match.is_relevant = is_relevant
        if notes:
            match.notes = notes

        await self.db.commit()
        await self.db.refresh(match)
        return match

    async def get_active_tasks(self) -> list[MonitorTask]:
        """Get all active monitoring tasks."""
        result = await self.db.execute(
            select(MonitorTask)
            .options(selectinload(MonitorTask.keywords))
            .where(MonitorTask.status == MonitorStatus.ACTIVE)
            .order_by(MonitorTask.last_check_at.asc().nulls_first())
        )
        return list(result.scalars().all())
