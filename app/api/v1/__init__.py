"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1 import celery_tasks, health, monitoring, vk, vk_integration, vk_test

# Create API router
router = APIRouter()

# Include all routers
router.include_router(health.router)
router.include_router(vk.router)
router.include_router(monitoring.router)
router.include_router(vk_integration.router)  # New VK integration endpoints
router.include_router(vk_test.router)  # VK API testing endpoints
router.include_router(celery_tasks.router)  # Celery task management

__all__ = ["router"]
