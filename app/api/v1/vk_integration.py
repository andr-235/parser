"""VK Integration API endpoints for real data fetching."""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.vk_client import init_vk_client
from app.schemas.monitoring import CommentMatchRead
from app.schemas.vk import VKCommentRead, VKPostRead, VKUserRead
from app.services.monitoring import MonitoringService
from app.services.vk_service import VKService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vk-integration", tags=["VK Integration"])


class VKSyncRequest(BaseModel):
    """Request model for VK data synchronization."""

    group_id: int
    posts_count: int = 20
    comments_per_post: int = 100


class VKKeywordSearchRequest(BaseModel):
    """Request model for keyword search."""

    group_id: int
    keywords: List[str]
    monitor_task_id: str
    limit: int = 100


@router.get("/health")
async def check_vk_health():
    """Check VK API connectivity and token validity."""
    try:
        is_connected = await init_vk_client()

        if is_connected:
            return {
                "status": "healthy",
                "vk_api": "connected",
                "message": "VK API is accessible",
            }
        else:
            return {
                "status": "unhealthy",
                "vk_api": "disconnected",
                "message": "VK API token invalid or API unreachable",
            }
    except Exception as e:
        logger.error(f"VK health check failed: {e}")
        return {
            "status": "error",
            "vk_api": "error",
            "message": f"VK API error: {str(e)}",
        }


@router.get("/group/{group_id}/info")
async def get_group_info(group_id: int, db: AsyncSession = Depends(get_db)):
    """Get VK group information from API."""
    try:
        vk_service = VKService(db)
        group_data = await vk_service.sync_group_info(group_id)

        if not group_data:
            raise HTTPException(
                status_code=404, detail=f"Group {group_id} not found or not accessible"
            )

        return group_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group info for {group_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch group information: {str(e)}"
        )


@router.post("/sync")
async def sync_vk_data(
    sync_request: VKSyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Sync VK data (posts, comments, users) to database."""
    try:
        vk_service = VKService(db)

        # Verify group exists
        group_data = await vk_service.sync_group_info(sync_request.group_id)
        if not group_data:
            raise HTTPException(
                status_code=404, detail=f"Group {sync_request.group_id} not found"
            )

        # Start background sync
        background_tasks.add_task(_background_sync_task, sync_request, db)

        return {
            "status": "started",
            "message": f"Data sync started for group {sync_request.group_id}",
            "group_name": group_data.get("name", "Unknown"),
            "estimated_time": "2-5 minutes",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")


@router.post("/search-keywords")
async def search_keywords_in_vk(
    search_request: VKKeywordSearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Search for keywords in VK comments."""
    try:
        # Start background keyword search
        background_tasks.add_task(_background_keyword_search, search_request, db)

        return {
            "status": "started",
            "message": f"Keyword search started for {len(search_request.keywords)} keywords",
            "keywords": search_request.keywords,
            "estimated_time": "1-3 minutes",
        }

    except Exception as e:
        logger.error(f"Error starting keyword search: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start keyword search: {str(e)}"
        )


async def _background_sync_task(sync_request: VKSyncRequest, db: AsyncSession):
    """Background task for syncing VK data."""
    vk_service = VKService(db)

    try:
        logger.info(f"Starting background sync for group {sync_request.group_id}")

        # Sync posts
        posts = await vk_service.sync_posts_data(
            sync_request.group_id, count=sync_request.posts_count
        )

        logger.info(f"Synced {len(posts)} posts")

        # Sync comments for each post
        total_comments = 0
        for post in posts:
            comments = await vk_service.sync_comments_data(
                sync_request.group_id,
                post.vk_post_id,
                count=sync_request.comments_per_post,
            )
            total_comments += len(comments)

        logger.info(f"Sync completed: {len(posts)} posts, {total_comments} comments")

    except Exception as e:
        logger.error(f"Background sync failed: {e}")


async def _background_keyword_search(
    search_request: VKKeywordSearchRequest, db: AsyncSession
):
    """Background task for keyword search."""
    vk_service = VKService(db)

    try:
        logger.info(f"Starting keyword search for {search_request.keywords}")

        matches = await vk_service.search_and_monitor_keywords(
            search_request.monitor_task_id,
            search_request.group_id,
            search_request.keywords,
        )

        # Update monitoring statistics
        await vk_service.update_monitoring_statistics(search_request.monitor_task_id)

        logger.info(f"Keyword search completed: {len(matches)} matches found")

    except Exception as e:
        logger.error(f"Background keyword search failed: {e}")


@router.get("/group/{group_id}/posts", response_model=List[VKPostRead])
async def get_synced_posts(
    group_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get synced VK posts from database."""
    try:
        vk_service = VKService(db)

        # This would need to be implemented in VKService
        # For now, return empty list with TODO
        return []

    except Exception as e:
        logger.error(f"Error getting posts for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get posts: {str(e)}")


@router.get("/group/{group_id}/comments", response_model=List[VKCommentRead])
async def get_synced_comments(
    group_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    hours_back: int = Query(24, ge=1, le=168),  # Max 1 week
    db: AsyncSession = Depends(get_db),
):
    """Get recent synced VK comments from database."""
    try:
        vk_service = VKService(db)
        comments = await vk_service.get_recent_comments_for_monitoring(
            group_id, hours_back=hours_back
        )

        # Apply pagination
        paginated_comments = comments[skip : skip + limit]

        return [VKCommentRead.model_validate(comment) for comment in paginated_comments]

    except Exception as e:
        logger.error(f"Error getting comments for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get comments: {str(e)}")


@router.get("/user/{user_id}", response_model=VKUserRead)
async def get_user_info(
    user_id: int,
    sync_fresh: bool = Query(False, description="Fetch fresh data from VK API"),
    db: AsyncSession = Depends(get_db),
):
    """Get VK user information."""
    try:
        vk_service = VKService(db)

        if sync_fresh:
            # Sync fresh data from VK API
            user = await vk_service.sync_user_data(user_id)
        else:
            # Get from database only (if exists)
            # This would need DB query implementation
            user = await vk_service.sync_user_data(user_id)

        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        return VKUserRead.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.post("/monitor-task/{task_id}/run")
async def run_monitoring_task(
    task_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """Run a monitoring task manually."""
    try:
        monitoring_service = MonitoringService(db)

        # Get the task
        task = await monitoring_service.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=404, detail=f"Monitoring task {task_id} not found"
            )

        # Start background monitoring
        background_tasks.add_task(_background_monitoring_task, task_id, db)

        return {
            "status": "started",
            "task_id": task_id,
            "message": "Monitoring task started",
            "estimated_time": "3-7 minutes",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running monitoring task {task_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to run monitoring task: {str(e)}"
        )


async def _background_monitoring_task(task_id: str, db: AsyncSession):
    """Background task for full monitoring."""
    try:
        logger.info(f"Starting monitoring task {task_id}")

        monitoring_service = MonitoringService(db)
        vk_service = VKService(db)

        # Get task details
        task = await monitoring_service.get_by_id(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        # Extract keywords
        keywords = [kw.word for kw in task.keywords]

        # Run keyword search for each group
        if task.vk_group_id:
            matches = await vk_service.search_and_monitor_keywords(
                task_id, task.vk_group_id, keywords
            )

            # Update statistics
            await vk_service.update_monitoring_statistics(task_id)

            logger.info(f"Monitoring task {task_id} completed: {len(matches)} matches")

    except Exception as e:
        logger.error(f"Background monitoring task {task_id} failed: {e}")


@router.get("/stats/sync-status")
async def get_sync_status(db: AsyncSession = Depends(get_db)):
    """Get VK data synchronization statistics."""
    try:
        # This would need to be implemented to show sync stats
        # For now, return basic info
        return {
            "status": "active",
            "last_sync": "2025-01-16T15:30:00Z",
            "total_groups": 0,
            "total_posts": 0,
            "total_comments": 0,
            "total_users": 0,
        }

    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync status: {str(e)}"
        )
