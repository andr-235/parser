"""VK service for managing VK entities."""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.vk import VKComment, VKPost, VKUser
from app.schemas.vk import VKCommentCreate, VKPostCreate, VKUserCreate


class VKService:
    """Service for managing VK entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # VK User methods
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[VKUser]:
        """Get VK user by internal ID."""
        result = await self.db.execute(select(VKUser).where(VKUser.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_vk_id(self, vk_id: int) -> Optional[VKUser]:
        """Get VK user by VK ID."""
        result = await self.db.execute(select(VKUser).where(VKUser.vk_id == vk_id))
        return result.scalar_one_or_none()

    async def get_users_paginated(
        self, offset: int = 0, limit: int = 50
    ) -> Tuple[List[VKUser], int]:
        """Get paginated list of VK users."""
        # Get total count
        count_result = await self.db.execute(select(func.count(VKUser.id)))
        total = count_result.scalar()

        # Get users
        result = await self.db.execute(
            select(VKUser)
            .offset(offset)
            .limit(limit)
            .order_by(VKUser.created_at.desc())
        )
        users = result.scalars().all()

        return list(users), total

    async def create_user(self, user_data: VKUserCreate) -> VKUser:
        """Create new VK user."""
        user = VKUser(**user_data.model_dump())
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(
        self, user_id: uuid.UUID, user_data: dict
    ) -> Optional[VKUser]:
        """Update VK user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        for field, value in user_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    # VK Post methods
    async def get_post_by_id(self, post_id: uuid.UUID) -> Optional[VKPost]:
        """Get VK post by internal ID."""
        result = await self.db.execute(
            select(VKPost)
            .options(selectinload(VKPost.author))
            .where(VKPost.id == post_id)
        )
        return result.scalar_one_or_none()

    async def get_post_by_vk_id(self, vk_id: int) -> Optional[VKPost]:
        """Get VK post by VK ID."""
        result = await self.db.execute(select(VKPost).where(VKPost.vk_id == vk_id))
        return result.scalar_one_or_none()

    async def get_posts_paginated(
        self, offset: int = 0, limit: int = 50, owner_id: Optional[int] = None
    ) -> Tuple[List[VKPost], int]:
        """Get paginated list of VK posts."""
        query = select(VKPost).options(selectinload(VKPost.author))
        count_query = select(func.count(VKPost.id))

        if owner_id:
            query = query.where(VKPost.owner_id == owner_id)
            count_query = count_query.where(VKPost.owner_id == owner_id)

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get posts
        result = await self.db.execute(
            query.offset(offset).limit(limit).order_by(VKPost.published_at.desc())
        )
        posts = result.scalars().all()

        return list(posts), total

    async def create_post(self, post_data: VKPostCreate) -> VKPost:
        """Create new VK post."""
        post = VKPost(**post_data.model_dump())
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    # VK Comment methods
    async def get_comment_by_id(self, comment_id: uuid.UUID) -> Optional[VKComment]:
        """Get VK comment by internal ID."""
        result = await self.db.execute(
            select(VKComment)
            .options(selectinload(VKComment.author), selectinload(VKComment.post))
            .where(VKComment.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def get_comment_by_vk_id(self, vk_id: int) -> Optional[VKComment]:
        """Get VK comment by VK ID."""
        result = await self.db.execute(
            select(VKComment).where(VKComment.vk_id == vk_id)
        )
        return result.scalar_one_or_none()

    async def get_comments_paginated(
        self,
        offset: int = 0,
        limit: int = 50,
        post_vk_id: Optional[int] = None,
        author_vk_id: Optional[int] = None,
        contains_keywords: Optional[bool] = None,
    ) -> Tuple[List[VKComment], int]:
        """Get paginated list of VK comments."""
        query = select(VKComment).options(
            selectinload(VKComment.author), selectinload(VKComment.post)
        )
        count_query = select(func.count(VKComment.id))

        # Apply filters
        if post_vk_id:
            query = query.where(VKComment.post_id == post_vk_id)
            count_query = count_query.where(VKComment.post_id == post_vk_id)

        if author_vk_id:
            query = query.where(VKComment.from_id == author_vk_id)
            count_query = count_query.where(VKComment.from_id == author_vk_id)

        if contains_keywords is not None:
            query = query.where(VKComment.contains_keywords == contains_keywords)
            count_query = count_query.where(
                VKComment.contains_keywords == contains_keywords
            )

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get comments
        result = await self.db.execute(
            query.offset(offset).limit(limit).order_by(VKComment.published_at.desc())
        )
        comments = result.scalars().all()

        return list(comments), total

    async def create_comment(self, comment_data: VKCommentCreate) -> VKComment:
        """Create new VK comment."""
        comment = VKComment(**comment_data.model_dump())
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def mark_comments_processed(self, comment_ids: List[uuid.UUID]) -> int:
        """Mark comments as processed."""
        from sqlalchemy import update

        result = await self.db.execute(
            update(VKComment)
            .where(VKComment.id.in_(comment_ids))
            .values(is_processed=True)
        )
        await self.db.commit()
        return result.rowcount

    async def get_unprocessed_comments(self, limit: int = 100) -> List[VKComment]:
        """Get unprocessed comments for analysis."""
        result = await self.db.execute(
            select(VKComment)
            .where(VKComment.is_processed == False)
            .order_by(VKComment.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_comments_by_text(
        self,
        search_text: str,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[VKComment], int]:
        """Search comments by text content."""
        # PostgreSQL full-text search
        query = (
            select(VKComment)
            .options(selectinload(VKComment.author), selectinload(VKComment.post))
            .where(VKComment.text.ilike(f"%{search_text}%"))
        )

        count_query = select(func.count(VKComment.id)).where(
            VKComment.text.ilike(f"%{search_text}%")
        )

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get comments
        result = await self.db.execute(
            query.offset(offset).limit(limit).order_by(VKComment.published_at.desc())
        )
        comments = result.scalars().all()

        return list(comments), total
