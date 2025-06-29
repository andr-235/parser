"""Health check endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()
# settings imported directly


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "message": "VK Comments Monitor is running",
    }


@router.get("/database")
async def database_health_check(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Database connectivity health check."""
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1 as test"))
        test_result = result.fetchone()

        if test_result and test_result[0] == 1:
            return {
                "status": "healthy",
                "service": "database",
                "message": "PostgreSQL connection successful",
                "connection": "active",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database query returned unexpected result",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}",
        ) from e


@router.get("/dependencies")
async def dependencies_check() -> Dict[str, Any]:
    """Check external dependencies status."""
    dependencies = {
        "database": {"status": "unknown", "message": "Not tested"},
        "redis": {"status": "unknown", "message": "Not tested"},
        "vk_api": {"status": "unknown", "message": "Not configured"},
    }

    # Test database
    try:
        from app.core.database import engine

        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        dependencies["database"] = {
            "status": "healthy",
            "message": "PostgreSQL connection active",
        }
    except Exception as e:
        dependencies["database"] = {
            "status": "unhealthy",
            "message": f"PostgreSQL error: {str(e)[:100]}",
        }

    # Test Redis (if configured)
    try:
        import redis.asyncio as redis

        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        dependencies["redis"] = {
            "status": "healthy",
            "message": "Redis connection active",
        }
    except Exception as e:
        dependencies["redis"] = {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)[:100]}",
        }

    # Check VK API token
    if settings.VK_API_TOKEN:
        dependencies["vk_api"] = {
            "status": "configured",
            "message": "VK API token is set",
        }
    else:
        dependencies["vk_api"] = {
            "status": "not_configured",
            "message": "VK API token not set",
        }

    # Overall status
    healthy_count = sum(
        1 for dep in dependencies.values() if dep["status"] in ["healthy", "configured"]
    )
    total_count = len(dependencies)

    overall_status = "healthy" if healthy_count == total_count else "degraded"

    return {
        "status": overall_status,
        "dependencies": dependencies,
        "summary": f"{healthy_count}/{total_count} dependencies healthy",
    }
