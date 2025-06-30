"""Celery application configuration and setup."""

import logging

from celery import Celery
from kombu import Queue

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "vk_monitor_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.vk_tasks",
        "app.workers.monitoring_tasks",
    ],
)

# Configure Celery
celery_app.conf.update(
    # Task routing and queues
    task_routes={
        "app.workers.vk_tasks.*": {"queue": "vk_api"},
        "app.workers.monitoring_tasks.*": {"queue": "monitoring"},
    },
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("vk_api", routing_key="vk_api"),
        Queue("monitoring", routing_key="monitoring"),
    ),
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task retries and timeouts
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Rate limiting for VK API compliance
    task_annotations={
        "app.workers.vk_tasks.scan_group_comments": {
            "rate_limit": "3/s",  # VK API limit: 3 requests per second
        },
        "app.workers.vk_tasks.fetch_vk_posts": {
            "rate_limit": "3/s",
        },
        "app.workers.vk_tasks.sync_vk_group": {
            "rate_limit": "1/s",
        },
    },
    # Monitoring and logging
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Redis backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
)

# Auto-discover tasks in modules
celery_app.autodiscover_tasks(
    [
        "app.workers.vk_tasks",
        "app.workers.monitoring_tasks",
    ]
)


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    logger.info(f"Debug task request: {self.request!r}")
    return {"status": "success", "message": "Celery is working!"}


if __name__ == "__main__":
    celery_app.start()
