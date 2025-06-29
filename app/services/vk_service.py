"""VK service for real data integration."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSession
from app.core.vk_client import VKClient, get_vk_client
from app.models.monitoring import CommentMatch, Keyword, MonitorTask
from app.models.vk import VKComment, VKPost, VKUser
from app.schemas.vk import VKCommentCreate, VKPostCreate, VKUserCreate

logger = logging.getLogger(__name__)


class VKService:
    """Service for VK API integration and data synchronization."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.vk_client = get_vk_client()  # Real VK client

    async def sync_group_info(self, group_id: int) -> Optional[dict]:
        """Sync VK group information."""
        try:
            group_data = await self.vk_client.get_group_info(group_id)

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
        """Sync VK user data from API to database."""
        try:
            # Check if user already exists
            result = await self.db.execute(
                select(VKUser).where(VKUser.vk_user_id == user_id)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.debug(f"User {user_id} already exists in database")
                return existing_user

            # Fetch user data from VK API
            user_data = await self.vk_client.get_user_info(user_id)

            if not user_data:
                logger.warning(
                    f"Could not fetch user data from VK API for user {user_id}"
                )
                return None

            # Create new user from VK API data
            new_user = VKUser(
                vk_user_id=user_data["vk_user_id"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                screen_name=user_data.get("screen_name"),
                photo_url=user_data.get("photo_url"),
                is_verified=user_data.get("is_verified", False),
                followers_count=user_data.get("followers_count", 0),
            )

            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)

            logger.info(f"Synced new user from VK API: {user_id}")
            return new_user

        except Exception as e:
            logger.error(f"Error syncing user {user_id}: {e}")
            await self.db.rollback()
            return None

    async def sync_posts_data(
        self, group_id: int, count: int = 20, offset: int = 0
    ) -> List[VKPost]:
        """Sync VK posts data from API to database."""
        synced_posts = []

        try:
            # Fetch posts from VK API
            posts_data = await self.vk_client.get_wall_posts(
                group_id=group_id, count=count, offset=offset
            )

            if not posts_data:
                logger.info(f"No posts fetched from VK API for group {group_id}")
                return synced_posts

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
                        # Update engagement metrics from fresh VK data
                        existing_post.likes_count = post_data.get("likes_count", 0)
                        existing_post.comments_count = post_data.get(
                            "comments_count", 0
                        )
                        existing_post.reposts_count = post_data.get("reposts_count", 0)

                        synced_posts.append(existing_post)
                        logger.debug(
                            f"Updated post {post_data['vk_post_id']} metrics from VK API"
                        )
                        continue

                    # Sync author if provided
                    author_id = post_data.get("author_id")
                    if author_id:
                        await self.sync_user_data(author_id)

                    # Create new post from VK API data
                    new_post = VKPost(
                        vk_post_id=post_data["vk_post_id"],
                        vk_group_id=post_data["vk_group_id"],
                        author_id=author_id,
                        text=post_data.get("text", ""),
                        date=post_data["date"],
                        likes_count=post_data.get("likes_count", 0),
                        comments_count=post_data.get("comments_count", 0),
                        reposts_count=post_data.get("reposts_count", 0),
                        post_url=post_data.get("post_url", ""),
                    )

                    self.db.add(new_post)
                    synced_posts.append(new_post)
                    logger.info(
                        f"Synced new post from VK API: {post_data['vk_post_id']}"
                    )

                except Exception as e:
                    logger.error(
                        f"Error processing post {post_data.get('vk_post_id')}: {e}"
                    )
                    continue

            await self.db.commit()

            # Refresh all synced posts
            for post in synced_posts:
                await self.db.refresh(post)

            logger.info(
                f"Synced {len(synced_posts)} posts from VK API for group {group_id}"
            )
            return synced_posts

        except Exception as e:
            logger.error(f"Error syncing posts for group {group_id}: {e}")
            await self.db.rollback()
            return []

    async def sync_comments_data(
        self, group_id: int, post_id: int, count: int = 100, offset: int = 0
    ) -> List[VKComment]:
        """Sync VK comments data from API to database."""
        synced_comments = []

        try:
            # Fetch comments from VK API
            comments_data = await self.vk_client.get_post_comments(
                group_id=group_id, post_id=post_id, count=count, offset=offset
            )

            if not comments_data:
                logger.info(f"No comments fetched from VK API for post {post_id}")
                return synced_comments

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

                    # Sync author if provided
                    author_id = comment_data.get("author_id")
                    if author_id:
                        await self.sync_user_data(author_id)

                    # Create new comment from VK API data
                    new_comment = VKComment(
                        vk_comment_id=comment_data["vk_comment_id"],
                        vk_post_id=comment_data["vk_post_id"],
                        vk_group_id=comment_data["vk_group_id"],
                        author_id=author_id,
                        author_name=comment_data.get("author_name"),
                        author_screen_name=comment_data.get("author_screen_name"),
                        text=comment_data.get("text", ""),
                        date=comment_data["date"],
                        comment_url=comment_data.get("comment_url", ""),
                    )

                    self.db.add(new_comment)
                    synced_comments.append(new_comment)
                    logger.info(
                        f"Synced new comment from VK API: {comment_data['vk_comment_id']}"
                    )

                except Exception as e:
                    logger.error(
                        f"Error processing comment {comment_data.get('vk_comment_id')}: {e}"
                    )
                    continue

            await self.db.commit()

            # Refresh all synced comments
            for comment in synced_comments:
                await self.db.refresh(comment)

            logger.info(
                f"Synced {len(synced_comments)} comments from VK API for post {post_id}"
            )
            return synced_comments

        except Exception as e:
            logger.error(f"Error syncing comments for post {post_id}: {e}")
            await self.db.rollback()
            return []

    async def search_and_monitor_keywords(
        self, monitor_task_id: str, group_id: int, keywords: List[str]
    ) -> List[CommentMatch]:
        """Search for keywords in VK comments using real VK API data."""
        matches = []

        try:
            # First, sync recent posts to ensure we have fresh data
            logger.info(
                f"Syncing recent posts for keyword monitoring in group {group_id}"
            )
            recent_posts = await self.sync_posts_data(group_id, count=20)

            # Sync comments for each recent post
            for post in recent_posts:
                try:
                    post_comments = await self.sync_comments_data(
                        group_id, post.vk_post_id, count=100
                    )

                    # Search for keywords in comments
                    for comment in post_comments:
                        comment_text_lower = comment.text.lower()

                        for keyword in keywords:
                            if keyword.lower() in comment_text_lower:
                                # Check if keyword exists in database
                                result = await self.db.execute(
                                    select(Keyword).where(
                                        and_(
                                            Keyword.word == keyword,
                                            Keyword.monitor_task_id == monitor_task_id,
                                        )
                                    )
                                )
                                keyword_obj = result.scalar_one_or_none()

                                if not keyword_obj:
                                    logger.warning(
                                        f"Keyword '{keyword}' not found in database"
                                    )
                                    continue

                                # Check if match already exists
                                result = await self.db.execute(
                                    select(CommentMatch).where(
                                        and_(
                                            CommentMatch.comment_id == comment.id,
                                            CommentMatch.keyword_id == keyword_obj.id,
                                        )
                                    )
                                )
                                existing_match = result.scalar_one_or_none()

                                if existing_match:
                                    continue

                                # Create new match
                                match = CommentMatch(
                                    monitor_task_id=monitor_task_id,
                                    comment_id=comment.id,
                                    keyword_id=keyword_obj.id,
                                    relevance_score=1.0,  # TODO: implement scoring
                                    matched_text=keyword,
                                    match_context=comment.text[:200],  # First 200 chars
                                )

                                self.db.add(match)
                                matches.append(match)
                                logger.info(
                                    f"Created keyword match for comment {comment.vk_comment_id} with keyword '{keyword}'"
                                )
                                break  # One match per comment

                except Exception as e:
                    logger.error(
                        f"Error processing post {post.vk_post_id} for keywords: {e}"
                    )
                    continue

            await self.db.commit()

            # Refresh all matches
            for match in matches:
                await self.db.refresh(match)

            logger.info(
                f"Created {len(matches)} keyword matches for task {monitor_task_id} using VK API data"
            )
            return matches

        except Exception as e:
            logger.error(f"Error in keyword monitoring for task {monitor_task_id}: {e}")
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
