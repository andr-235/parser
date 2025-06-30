"""Celery tasks for VK API operations."""

import asyncio
import logging

from celery import current_task
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.services.vk_service import VKService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Create async engine for Celery tasks
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)


async def get_db_session() -> AsyncSession:
    """Get database session for Celery tasks."""
    async with AsyncSessionLocal() as session:
        return session


@celery_app.task(bind=True, name="vk_tasks.scan_group_comments")
def scan_group_comments(
    self, group_id: int, keywords: list[str], monitor_task_id: str | None = None
):
    """
    Scan VK group comments for keywords.

    Args:
        group_id: VK group ID to scan
        keywords: List of keywords to search for
        monitor_task_id: Optional monitoring task ID for tracking
    """
    try:
        # Update task status
        current_task.update_state(state="PROGRESS", meta={"stage": "initializing"})

        # Run async operation
        result = asyncio.run(
            _scan_group_comments_async(group_id, keywords, monitor_task_id)
        )

        logger.info(f"Scan completed for group {group_id}: {result}")
        return result

    except Exception as e:
        logger.exception(f"Error scanning group {group_id}: {e}")
        current_task.update_state(
            state="FAILURE", meta={"error": str(e), "group_id": group_id}
        )
        raise


async def _scan_group_comments_async(
    group_id: int, keywords: list[str], monitor_task_id: str | None = None
) -> dict:
    """Async implementation of comment scanning."""
    async with AsyncSessionLocal() as db:
        try:
            # Update task progress
            current_task.update_state(
                state="PROGRESS", meta={"stage": "connecting_vk_api"}
            )

            # Initialize VK service
            vk_service = VKService(db)

            # Update task progress
            current_task.update_state(
                state="PROGRESS", meta={"stage": "fetching_posts"}
            )

            # Sync group posts first
            posts = await vk_service.sync_posts_data(group_id, count=50)
            logger.info(f"Synced {len(posts)} posts for group {group_id}")

            total_comments = 0
            total_matches = 0

            # Process each post
            for i, post in enumerate(posts):
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "stage": "processing_posts",
                        "current_post": i + 1,
                        "total_posts": len(posts),
                    },
                )

                # Sync comments for this post
                comments = await vk_service.sync_comments_data(
                    group_id, post.vk_post_id, count=100
                )
                total_comments += len(comments)

                # Search for keywords in comments
                if monitor_task_id:
                    matches = await vk_service.search_and_monitor_keywords(
                        monitor_task_id, group_id, keywords
                    )
                    total_matches += len(matches)

            # Update monitoring statistics if task ID provided
            if monitor_task_id:
                await vk_service.update_monitoring_statistics(monitor_task_id)

            return {
                "status": "completed",
                "group_id": group_id,
                "posts_processed": len(posts),
                "comments_found": total_comments,
                "keyword_matches": total_matches,
                "keywords": keywords,
            }

        except Exception as e:
            logger.exception(f"Error in async scan: {e}")
            raise


@celery_app.task(bind=True, name="vk_tasks.sync_vk_group")
def sync_vk_group(
    self, group_id: int, posts_count: int = 20, comments_per_post: int = 100
):
    """
    Synchronize VK group data (posts, comments, users).

    Args:
        group_id: VK group ID to sync
        posts_count: Number of posts to fetch
        comments_per_post: Number of comments per post
    """
    try:
        current_task.update_state(state="PROGRESS", meta={"stage": "starting_sync"})

        result = asyncio.run(
            _sync_vk_group_async(group_id, posts_count, comments_per_post)
        )

        logger.info(f"Group sync completed for {group_id}: {result}")
        return result

    except Exception as e:
        logger.exception(f"Error syncing group {group_id}: {e}")
        current_task.update_state(
            state="FAILURE", meta={"error": str(e), "group_id": group_id}
        )
        raise


async def _sync_vk_group_async(
    group_id: int, posts_count: int, comments_per_post: int
) -> dict:
    """Async implementation of group synchronization."""
    async with AsyncSessionLocal() as db:
        try:
            current_task.update_state(
                state="PROGRESS", meta={"stage": "initializing_services"}
            )

            vk_service = VKService(db)

            # Sync group info
            current_task.update_state(
                state="PROGRESS", meta={"stage": "syncing_group_info"}
            )
            group_data = await vk_service.sync_group_info(group_id)

            # Sync posts
            current_task.update_state(state="PROGRESS", meta={"stage": "syncing_posts"})
            posts = await vk_service.sync_posts_data(group_id, count=posts_count)

            total_comments = 0
            total_users = set()

            # Sync comments for each post
            for i, post in enumerate(posts):
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "stage": "syncing_comments",
                        "current_post": i + 1,
                        "total_posts": len(posts),
                    },
                )

                comments = await vk_service.sync_comments_data(
                    group_id, post.vk_post_id, count=comments_per_post
                )
                total_comments += len(comments)

                # Collect unique user IDs
                for comment in comments:
                    total_users.add(comment.author_id)

            return {
                "status": "completed",
                "group_id": group_id,
                "group_name": (
                    group_data.get("name", "Unknown") if group_data else "Unknown"
                ),
                "posts_synced": len(posts),
                "comments_synced": total_comments,
                "unique_users": len(total_users),
            }

        except Exception as e:
            logger.exception(f"Error in async group sync: {e}")
            raise


@celery_app.task(bind=True, name="vk_tasks.fetch_vk_posts")
def fetch_vk_posts(self, group_id: int, count: int = 50, offset: int = 0):
    """
    Fetch VK posts for a specific group.

    Args:
        group_id: VK group ID
        count: Number of posts to fetch
        offset: Offset for pagination
    """
    try:
        current_task.update_state(state="PROGRESS", meta={"stage": "fetching_posts"})

        result = asyncio.run(_fetch_vk_posts_async(group_id, count, offset))

        logger.info(
            f"Posts fetch completed for group {group_id}: {len(result.get('posts', []))} posts"
        )
        return result

    except Exception as e:
        logger.exception(f"Error fetching posts for group {group_id}: {e}")
        current_task.update_state(
            state="FAILURE", meta={"error": str(e), "group_id": group_id}
        )
        raise


async def _fetch_vk_posts_async(group_id: int, count: int, offset: int) -> dict:
    """Async implementation of posts fetching."""
    async with AsyncSessionLocal() as db:
        try:
            vk_service = VKService(db)

            posts = await vk_service.sync_posts_data(
                group_id, count=count, offset=offset
            )

            return {
                "status": "completed",
                "group_id": group_id,
                "posts_count": len(posts),
                "posts": [
                    {
                        "vk_post_id": post.vk_post_id,
                        "text": (
                            post.text[:100] + "..."
                            if len(post.text) > 100
                            else post.text
                        ),
                        "date": post.date.isoformat(),
                        "likes_count": post.likes_count,
                        "comments_count": post.comments_count,
                    }
                    for post in posts
                ],
            }

        except Exception as e:
            logger.exception(f"Error in async posts fetch: {e}")
            raise
