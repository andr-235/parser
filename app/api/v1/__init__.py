"""API v1 router setup."""

from fastapi import APIRouter

from app.api.v1 import health, monitoring, vk

api_router = APIRouter(prefix="/api/v1")

# Include routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(vk.router, prefix="/vk", tags=["vk"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])

__all__ = ["api_router"]
