"""Celery tasks for monitoring and scheduled operations."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from celery import current_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.monitoring import MonitorStatus, MonitorTask
from app.services.monitoring import MonitoringService
from app.services.vk_service import VKService
from app.workers.celery_app import celery_app
from app.workers.vk_tasks import scan_group_comments

logger = logging.getLogger(__name__)

# Create async engine for monitoring tasks
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)


@celery_app.task(bind=True, name="monitoring_tasks.run_scheduled_monitoring")
def run_scheduled_monitoring(self):
    """
    Run all active monitoring tasks that are due for execution.
    This is typically called by Celery Beat scheduler.
    """
    try:
        current_task.update_state(state="PROGRESS", meta={"stage": "checking_tasks"})

        result = asyncio.run(_run_scheduled_monitoring_async())

        logger.info(f"Scheduled monitoring completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in scheduled monitoring: {e}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise


async def _run_scheduled_monitoring_async() -> Dict:
    """Async implementation of scheduled monitoring."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all active monitoring tasks
            result = await db.execute(
                select(MonitorTask).where(MonitorTask.status == MonitorStatus.ACTIVE)
            )
            active_tasks = result.scalars().all()

            tasks_run = 0
            tasks_scheduled = 0

            current_time = datetime.utcnow()

            for task in active_tasks:
                # Check if task is due for execution
                if task.last_check_at is None:
                    # First run - schedule immediately
                    should_run = True
                else:
                    # Check if enough time has passed
                    next_run = task.last_check_at + timedelta(
                        minutes=task.check_interval_minutes
                    )
                    should_run = current_time >= next_run

                if should_run:
                    # Extract keywords for this task
                    keywords = [kw.word for kw in task.keywords]

                    if keywords and task.target_type == "group":
                        # Schedule VK scan task
                        scan_group_comments.delay(
                            group_id=task.target_id,
                            keywords=keywords,
                            monitor_task_id=str(task.id),
                        )

                        # Update last check time
                        task.last_check_at = current_time
                        tasks_scheduled += 1

                        logger.info(
                            f"Scheduled scan for task {task.id} "
                            f"(group {task.target_id}, {len(keywords)} keywords)"
                        )

                tasks_run += 1

            await db.commit()

            return {
                "status": "completed",
                "tasks_checked": tasks_run,
                "tasks_scheduled": tasks_scheduled,
                "timestamp": current_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in scheduled monitoring async: {e}")
            raise


@celery_app.task(bind=True, name="monitoring_tasks.execute_monitoring_task")
def execute_monitoring_task(self, task_id: str):
    """
    Execute a specific monitoring task manually.

    Args:
        task_id: Monitoring task ID to execute
    """
    try:
        current_task.update_state(
            state="PROGRESS", meta={"stage": "initializing", "task_id": task_id}
        )

        result = asyncio.run(_execute_monitoring_task_async(task_id))

        logger.info(f"Monitoring task {task_id} executed: {result}")
        return result

    except Exception as e:
        logger.error(f"Error executing monitoring task {task_id}: {e}")
        current_task.update_state(
            state="FAILURE", meta={"error": str(e), "task_id": task_id}
        )
        raise


async def _execute_monitoring_task_async(task_id: str) -> Dict:
    """Async implementation of single task execution."""
    async with AsyncSessionLocal() as db:
        try:
            monitoring_service = MonitoringService(db)

            # Get task details
            task = await monitoring_service.get_task_by_id(task_id)
            if not task:
                raise ValueError(f"Monitoring task {task_id} not found")

            current_task.update_state(
                state="PROGRESS", meta={"stage": "running_scan", "task_name": task.name}
            )

            # Extract keywords
            keywords = [kw.word for kw in task.keywords]

            if not keywords:
                logger.warning(f"No keywords found for task {task_id}")
                return {"status": "skipped", "reason": "no_keywords"}

            # Execute scan based on target type
            if task.target_type == "group":
                # Run VK group scan
                scan_result = await asyncio.create_task(
                    _run_vk_scan_for_task(task.target_id, keywords, task_id)
                )

                # Update task statistics
                task.last_check_at = datetime.utcnow()
                if "keyword_matches" in scan_result:
                    task.total_matches_found += scan_result["keyword_matches"]
                if "comments_found" in scan_result:
                    task.total_comments_found += scan_result["comments_found"]

                await db.commit()

                return {
                    "status": "completed",
                    "task_id": task_id,
                    "target_type": task.target_type,
                    "target_id": task.target_id,
                    "keywords_count": len(keywords),
                    "scan_result": scan_result,
                }
            else:
                return {
                    "status": "skipped",
                    "reason": f"unsupported_target_type_{task.target_type}",
                }

        except Exception as e:
            logger.error(f"Error in monitoring task execution async: {e}")
            raise


async def _run_vk_scan_for_task(
    group_id: int, keywords: List[str], task_id: str
) -> Dict:
    """Run VK scan for monitoring task."""
    async with AsyncSessionLocal() as db:
        vk_service = VKService(db)

        try:
            # Search for keywords in VK data
            matches = await vk_service.search_and_monitor_keywords(
                task_id, group_id, keywords
            )

            # Update monitoring statistics
            await vk_service.update_monitoring_statistics(task_id)

            return {
                "status": "completed",
                "group_id": group_id,
                "keyword_matches": len(matches),
                "keywords": keywords,
            }

        except Exception as e:
            logger.error(f"Error in VK scan for task {task_id}: {e}")
            return {"status": "error", "error": str(e), "group_id": group_id}


@celery_app.task(bind=True, name="monitoring_tasks.cleanup_old_data")
def cleanup_old_data(self, days_to_keep: int = 30):
    """
    Clean up old monitoring data.

    Args:
        days_to_keep: Number of days to keep data (default: 30)
    """
    try:
        current_task.update_state(
            state="PROGRESS",
            meta={"stage": "starting_cleanup", "days_to_keep": days_to_keep},
        )

        result = asyncio.run(_cleanup_old_data_async(days_to_keep))

        logger.info(f"Data cleanup completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in data cleanup: {e}")
        current_task.update_state(state="FAILURE", meta={"error": str(e)})
        raise


async def _cleanup_old_data_async(days_to_keep: int) -> Dict:
    """Async implementation of data cleanup."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # In a real implementation, you would:
        # - Query the database for old records
        # - Delete records older than cutoff_date
        # - Return statistics about what was cleaned up

        # Example: Delete old comments, matches, etc.

        logger.info(f"Data cleanup would remove data older than {cutoff_date}")

        return {
            "status": "success",
            "cutoff_date": cutoff_date.isoformat(),
            "cleanup_summary": "Dry run - no data actually removed",
        }
    except Exception as e:
        logger.exception(f"Error in cleanup task: {e}")
        raise


@celery_app.task(bind=True, name="monitoring_tasks.health_check")
def health_check(self):
    """
    Health check task to verify Celery workers are functioning.

    Returns:
        dict: Health status information
    """
    try:
        return {
            "status": "healthy",
            "worker_id": self.request.id,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.exception(f"Error in health check: {e}")
        raise
