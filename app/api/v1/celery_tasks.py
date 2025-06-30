"""API endpoints for Celery task management."""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.workers.celery_app import celery_app
from app.workers.monitoring_tasks import (
    cleanup_old_data,
    execute_monitoring_task,
    health_check,
    run_scheduled_monitoring,
)
from app.workers.vk_tasks import fetch_vk_posts, scan_group_comments, sync_vk_group

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/celery", tags=["Celery Tasks"])


class VKScanRequest(BaseModel):
    """Request model for VK scanning task."""

    group_id: int
    keywords: list[str]
    monitor_task_id: str | None = None


class VKSyncRequest(BaseModel):
    """Request model for VK sync task."""

    group_id: int
    posts_count: int = 20
    comments_per_post: int = 100


class MonitoringTaskRequest(BaseModel):
    """Request model for monitoring task execution."""

    task_id: str


class TaskResult(BaseModel):
    """Response model for task results."""

    task_id: str
    status: str
    message: str
    result: dict | None = None


@router.post("/vk/scan", response_model=TaskResult)
async def start_vk_scan(request: VKScanRequest):
    """
    Start a VK group comment scanning task.

    This will scan VK group comments for specified keywords
    and optionally link results to a monitoring task.
    """
    try:
        # Schedule Celery task
        task = scan_group_comments.delay(
            group_id=request.group_id,
            keywords=request.keywords,
            monitor_task_id=request.monitor_task_id,
        )

        logger.info(f"VK scan task started: {task.id} for group {request.group_id}")

        return TaskResult(
            task_id=task.id,
            status="started",
            message=f"VK scan started for group {request.group_id} with {len(request.keywords)} keywords",
            result={
                "group_id": request.group_id,
                "keywords_count": len(request.keywords),
                "monitor_task_id": request.monitor_task_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error starting VK scan: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start VK scan: {e!s}"
        ) from e


@router.post("/vk/sync", response_model=TaskResult)
async def start_vk_sync(request: VKSyncRequest):
    """
    Start a VK group data synchronization task.

    This will sync posts, comments, and users from a VK group.
    """
    try:
        # Schedule Celery task
        task = sync_vk_group.delay(
            group_id=request.group_id,
            posts_count=request.posts_count,
            comments_per_post=request.comments_per_post,
        )

        logger.info(f"VK sync task started: {task.id} for group {request.group_id}")

        return TaskResult(
            task_id=task.id,
            status="started",
            message=f"VK sync started for group {request.group_id}",
            result={
                "group_id": request.group_id,
                "posts_count": request.posts_count,
                "comments_per_post": request.comments_per_post,
            },
        )

    except Exception as e:
        logger.exception(f"Error starting VK sync: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start VK sync: {e!s}"
        ) from e


@router.post("/vk/fetch-posts", response_model=TaskResult)
async def start_vk_fetch_posts(
    group_id: int,
    count: int = Query(50, description="Number of posts to fetch"),
    offset: int = Query(0, description="Offset for pagination"),
):
    """
    Start a VK posts fetching task.

    This will fetch posts from a VK group without full synchronization.
    """
    try:
        # Schedule Celery task
        task = fetch_vk_posts.delay(group_id=group_id, count=count, offset=offset)

        logger.info(f"VK posts fetch task started: {task.id} for group {group_id}")

        return TaskResult(
            task_id=task.id,
            status="started",
            message=f"VK posts fetch started for group {group_id}",
            result={"group_id": group_id, "count": count, "offset": offset},
        )

    except Exception as e:
        logger.exception(f"Error starting VK posts fetch: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start VK posts fetch: {e!s}"
        ) from e


@router.post("/monitoring/execute", response_model=TaskResult)
async def start_monitoring_task(request: MonitoringTaskRequest):
    """
    Execute a specific monitoring task.

    This will run the monitoring task immediately, regardless of schedule.
    """
    try:
        # Schedule Celery task
        task = execute_monitoring_task.delay(request.task_id)

        logger.info(
            f"Monitoring task execution started: {task.id} for task {request.task_id}"
        )

        return TaskResult(
            task_id=task.id,
            status="started",
            message=f"Monitoring task execution started for {request.task_id}",
            result={"monitor_task_id": request.task_id},
        )

    except Exception as e:
        logger.exception(f"Error starting monitoring task: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start monitoring task: {e!s}"
        ) from e


@router.post("/monitoring/run-scheduled", response_model=TaskResult)
async def start_scheduled_monitoring():
    """
    Run all scheduled monitoring tasks.

    This checks all active monitoring tasks and runs those that are due.
    """
    try:
        # Schedule Celery task
        task = run_scheduled_monitoring.delay()

        logger.info(f"Scheduled monitoring task started: {task.id}")

        return TaskResult(
            task_id=task.id,
            status="started",
            message="Scheduled monitoring check started",
            result={},
        )

    except Exception as e:
        logger.exception(f"Error starting scheduled monitoring: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start scheduled monitoring: {e!s}"
        ) from e


@router.post("/cleanup", response_model=TaskResult)
async def start_cleanup_task(
    days_to_keep: int = Query(30, description="Number of days to keep data"),
):
    """
    Start a data cleanup task.

    This will clean up old monitoring data based on retention policy.
    """
    try:
        # Schedule Celery task
        task = cleanup_old_data.delay(days_to_keep=days_to_keep)

        logger.info(f"Cleanup task started: {task.id} (keeping {days_to_keep} days)")

        return TaskResult(
            task_id=task.id,
            status="started",
            message=f"Data cleanup started (keeping {days_to_keep} days)",
            result={"days_to_keep": days_to_keep},
        )

    except Exception as e:
        logger.exception(f"Error starting cleanup task: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start cleanup task: {e!s}"
        ) from e


@router.get("/health", response_model=TaskResult)
async def start_health_check():
    """
    Start a Celery worker health check task.

    This verifies that Celery workers are operational.
    """
    try:
        # Schedule Celery task
        task = health_check.delay()

        logger.info(f"Health check task started: {task.id}")

        return TaskResult(
            task_id=task.id,
            status="started",
            message="Celery health check started",
            result={},
        )

    except Exception as e:
        logger.exception(f"Error starting health check: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start health check: {e!s}"
        ) from e


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a Celery task.

    Args:
        task_id: Celery task ID to check
    """
    try:
        # Get task result
        result = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "failed": result.failed() if result.ready() else None,
        }

        # Add result/error info if available
        if result.ready():
            if result.successful():
                response["result"] = result.result
            elif result.failed():
                response["error"] = str(result.result)
        else:
            # Task is still running, check for progress info
            if result.state == "PROGRESS":
                response["progress"] = result.info

        return response

    except Exception as e:
        logger.exception(f"Error getting task status for {task_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {e!s}"
        ) from e


@router.get("/active-tasks")
async def get_active_tasks():
    """
    Get list of active Celery tasks.

    This shows currently running tasks across all workers.
    """
    try:
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        if not active_tasks:
            return {"active_tasks": [], "workers": 0}

        # Format response
        all_tasks = []
        for worker_name, tasks in active_tasks.items():
            for task in tasks:
                all_tasks.append(
                    {
                        "worker": worker_name,
                        "task_id": task["id"],
                        "name": task["name"],
                        "args": task.get("args", []),
                        "kwargs": task.get("kwargs", {}),
                        "time_start": task.get("time_start"),
                    }
                )

        return {
            "active_tasks": all_tasks,
            "workers": len(active_tasks),
            "total_tasks": len(all_tasks),
        }

    except Exception as e:
        logger.exception(f"Error getting active tasks: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get active tasks: {e!s}"
        ) from e


@router.get("/workers")
async def get_worker_stats():
    """
    Get Celery worker statistics.

    This shows information about available workers.
    """
    try:
        inspect = celery_app.control.inspect()

        # Get worker stats
        stats = inspect.stats()
        registered = inspect.registered()
        active = inspect.active()

        workers_info = []

        if stats:
            for worker_name, worker_stats in stats.items():
                worker_info = {
                    "name": worker_name,
                    "status": "online",
                    "processes": worker_stats.get("pool", {}).get("processes", 0),
                    "registered_tasks": (
                        len(registered.get(worker_name, [])) if registered else 0
                    ),
                    "active_tasks": len(active.get(worker_name, [])) if active else 0,
                    "load": worker_stats.get("rusage", {}),
                }
                workers_info.append(worker_info)

        return {
            "workers": workers_info,
            "total_workers": len(workers_info),
            "online_workers": len([w for w in workers_info if w["status"] == "online"]),
        }

    except Exception as e:
        logger.exception(f"Error getting worker stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get worker stats: {e!s}"
        ) from e
