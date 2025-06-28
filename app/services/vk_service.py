"""VK service for real data integration."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.vk_client import VKClient, get_vk_client
from app.models.monitoring import CommentMatch, Keyword, MonitorTask
from app.models.vk import VKComment, VKPost, VKUser
from app.schemas.vk import VKCommentCreate, VKPostCreate, VKUserCreate

logger = logging.getLogger(__name__)


class VKService:
    """Service for VK API integration and data synchronization."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.vk_client: Optional[VKClient] = None

    async def _get_vk_client(self) -> VKClient:
        """Get VK API client."""
        if self.vk_client is None:
            self.vk_client = get_vk_client()
        return self.vk_client

    async def sync_group_info(self, group_id: int) -> Optional[dict]:
        """Sync VK group information."""
        try:
            client = await self._get_vk_client()
            group_data = await client.get_group_info(group_id)

            if group_data:
                logger.info(f"Synced group info for {group_id}: {group_data['name']}")
                return group_data
            else:
                logger.warning(f"Could not fetch group info for {group_id}")
                return None

        except Exception as e:
            logger.error(f"Error syncing group {group_id}: {e}")
            return None

    async def sync_user_data(self, user_id: int) -> Optional[VKUser]:
        """Sync VK user data to database."""
        try:
            # Check if user already exists
            result = await self.db.execute(
                select(VKUser).where(VKUser.vk_user_id == user_id)
            )
            existing_user = result.scalar_one_or_none()

            # Get fresh data from VK API
            client = await self._get_vk_client()
            user_data = await client.get_user_info(user_id)

            if not user_data:
                logger.warning(f"Could not fetch user data for {user_id}")
                return existing_user

            if existing_user:
                # Update existing user
                for key, value in user_data.items():
                    if hasattr(existing_user, key):
                        setattr(existing_user, key, value)

                await self.db.commit()
                await self.db.refresh(existing_user)
                logger.info(f"Updated user {user_id}")
                return existing_user
            else:
                # Create new user
                user_create = VKUserCreate(**user_data)
                new_user = VKUser(**user_create.model_dump())

                self.db.add(new_user)
                await self.db.commit()
                await self.db.refresh(new_user)
                logger.info(f"Created new user {user_id}")
                return new_user

        except Exception as e:
            logger.error(f"Error syncing user {user_id}: {e}")
            await self.db.rollback()
            return None

    async def sync_posts_data(
        self, group_id: int, count: int = 20, offset: int = 0
    ) -> List[VKPost]:
        """Sync VK posts data to database."""
        synced_posts = []

        try:
            client = await self._get_vk_client()
            posts_data = await client.get_wall_posts(group_id, count, offset)

            for post_data in posts_data:
                try:
                    # Check if post already exists
                    result = await self.db.execute(
                        select(VKPost).where(
                            and_(
                                VKPost.vk_post_id == post_data["vk_post_id"],
                                VKPost.vk_group_id == group_id,
                            )
                        )
                    )
                    existing_post = result.scalar_one_or_none()

                    if existing_post:
                        # Update engagement metrics
                        existing_post.likes_count = post_data.get("likes_count", 0)
                        existing_post.comments_count = post_data.get(
                            "comments_count", 0
                        )
                        existing_post.reposts_count = post_data.get("reposts_count", 0)

                        synced_posts.append(existing_post)
                        logger.debug(f"Updated post {post_data['vk_post_id']}")
                    else:
                        # Sync author user data
                        author_id = post_data.get("author_id")
                        if author_id:
                            await self.sync_user_data(author_id)

                        # Create new post
                        post_create = VKPostCreate(**post_data)
                        new_post = VKPost(**post_create.model_dump())

                        self.db.add(new_post)
                        synced_posts.append(new_post)
                        logger.info(f"Created new post {post_data['vk_post_id']}")

                except Exception as e:
                    logger.error(
                        f"Error processing post {post_data.get('vk_post_id')}: {e}"
                    )
                    continue

            await self.db.commit()

            # Refresh all objects
            for post in synced_posts:
                await self.db.refresh(post)

            logger.info(f"Synced {len(synced_posts)} posts for group {group_id}")
            return synced_posts

        except Exception as e:
            logger.error(f"Error syncing posts for group {group_id}: {e}")
            await self.db.rollback()
            return []

    async def sync_comments_data(
        self, group_id: int, post_id: int, count: int = 100, offset: int = 0
    ) -> List[VKComment]:
        """Sync VK comments data to database."""
        synced_comments = []

        try:
            client = await self._get_vk_client()
            comments_data = await client.get_post_comments(
                group_id, post_id, count, offset
            )

            for comment_data in comments_data:
                try:
                    # Check if comment already exists
                    result = await self.db.execute(
                        select(VKComment).where(
                            and_(
                                VKComment.vk_comment_id
                                == comment_data["vk_comment_id"],
                                VKComment.vk_post_id == post_id,
                            )
                        )
                    )
                    existing_comment = result.scalar_one_or_none()

                    if existing_comment:
                        synced_comments.append(existing_comment)
                        logger.debug(
                            f"Comment {comment_data['vk_comment_id']} already exists"
                        )
                        continue

                    # Sync author user data
                    author_id = comment_data.get("author_id")
                    if author_id:
                        await self.sync_user_data(author_id)

                    # Create new comment
                    comment_create = VKCommentCreate(**comment_data)
                    new_comment = VKComment(**comment_create.model_dump())

                    self.db.add(new_comment)
                    synced_comments.append(new_comment)
                    logger.info(f"Created new comment {comment_data['vk_comment_id']}")

                except Exception as e:
                    logger.error(
                        f"Error processing comment {comment_data.get('vk_comment_id')}: {e}"
                    )
                    continue

            await self.db.commit()

            # Refresh all objects
            for comment in synced_comments:
                await self.db.refresh(comment)

            logger.info(f"Synced {len(synced_comments)} comments for post {post_id}")
            return synced_comments

        except Exception as e:
            logger.error(f"Error syncing comments for post {post_id}: {e}")
            await self.db.rollback()
            return []

    async def search_and_monitor_keywords(
        self, monitor_task_id: str, group_id: int, keywords: List[str]
    ) -> List[CommentMatch]:
        """Search for keywords in VK comments and create matches."""
        matches = []

        try:
            # Get the monitor task
            result = await self.db.execute(
                select(MonitorTask)
                .options(selectinload(MonitorTask.keywords))
                .where(MonitorTask.id == monitor_task_id)
            )
            monitor_task = result.scalar_one_or_none()

            if not monitor_task:
                logger.error(f"Monitor task {monitor_task_id} not found")
                return []

            # Search comments via VK API
            client = await self._get_vk_client()
            found_comments = await client.search_comments_by_keywords(
                group_id, keywords, limit=100
            )

            for comment_data in found_comments:
                try:
                    # Sync comment to database first
                    vk_comment_id = comment_data["vk_comment_id"]
                    vk_post_id = comment_data["vk_post_id"]

                    # Check if comment exists in DB
                    result = await self.db.execute(
                        select(VKComment).where(
                            and_(
                                VKComment.vk_comment_id == vk_comment_id,
                                VKComment.vk_post_id == vk_post_id,
                            )
                        )
                    )
                    comment = result.scalar_one_or_none()

                    if not comment:
                        # Sync the comment
                        comments = await self.sync_comments_data(
                            group_id, vk_post_id, count=100
                        )
                        # Find our comment
                        comment = next(
                            (c for c in comments if c.vk_comment_id == vk_comment_id),
                            None,
                        )

                    if not comment:
                        logger.warning(f"Could not sync comment {vk_comment_id}")
                        continue

                    # Find matching keyword
                    matched_keyword = comment_data.get("matched_keyword")
                    if matched_keyword:
                        # Get keyword from DB
                        result = await self.db.execute(
                            select(Keyword).where(
                                and_(
                                    Keyword.word == matched_keyword,
                                    Keyword.monitor_task_id == monitor_task_id,
                                )
                            )
                        )
                        keyword = result.scalar_one_or_none()

                        if keyword:
                            # Check if match already exists
                            result = await self.db.execute(
                                select(CommentMatch).where(
                                    and_(
                                        CommentMatch.comment_id == comment.id,
                                        CommentMatch.keyword_id == keyword.id,
                                    )
                                )
                            )
                            existing_match = result.scalar_one_or_none()

                            if not existing_match:
                                # Create new match
                                match = CommentMatch(
                                    comment_id=comment.id,
                                    keyword_id=keyword.id,
                                    monitor_task_id=monitor_task_id,
                                    relevance_score=1.0,  # TODO: implement scoring
                                    matched_text=matched_keyword,
                                    match_context=comment.text[:200],  # First 200 chars
                                )

                                self.db.add(match)
                                matches.append(match)
                                logger.info(
                                    f"Created keyword match for comment {vk_comment_id}"
                                )

                except Exception as e:
                    logger.error(f"Error processing keyword match: {e}")
                    continue

            await self.db.commit()

            # Refresh all matches
            for match in matches:
                await self.db.refresh(match)

            logger.info(
                f"Created {len(matches)} keyword matches for task {monitor_task_id}"
            )
            return matches

        except Exception as e:
            logger.error(f"Error in keyword monitoring: {e}")
            await self.db.rollback()
            return []

    async def get_recent_comments_for_monitoring(
        self, group_id: int, hours_back: int = 24
    ) -> List[VKComment]:
        """Get recent comments for monitoring from database."""
        try:
            since_date = datetime.utcnow() - timedelta(hours=hours_back)

            result = await self.db.execute(
                select(VKComment)
                .where(
                    and_(
                        VKComment.vk_group_id == group_id, VKComment.date >= since_date
                    )
                )
                .order_by(VKComment.date.desc())
                .limit(1000)
            )

            comments = result.scalars().all()
            logger.info(
                f"Retrieved {len(comments)} recent comments for group {group_id}"
            )
            return list(comments)

        except Exception as e:
            logger.error(f"Error getting recent comments: {e}")
            return []

    async def update_monitoring_statistics(self, monitor_task_id: str) -> bool:
        """Update statistics for monitoring task."""
        try:
            # Get total matches count
            result = await self.db.execute(
                select(CommentMatch).where(
                    CommentMatch.monitor_task_id == monitor_task_id
                )
            )
            total_matches = len(result.scalars().all())

            # Update monitor task
            result = await self.db.execute(
                select(MonitorTask).where(MonitorTask.id == monitor_task_id)
            )
            monitor_task = result.scalar_one_or_none()

            if monitor_task:
                monitor_task.total_matches = total_matches
                monitor_task.last_check = datetime.utcnow()
                await self.db.commit()

                logger.info(
                    f"Updated statistics for task {monitor_task_id}: {total_matches} matches"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating monitoring statistics: {e}")
            await self.db.rollback()
            return False
