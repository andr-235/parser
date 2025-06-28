"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import create_tables, get_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await create_tables()
    yield
    # Shutdown
    pass


# FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="VK Comments monitoring and analysis system with keyword tracking",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "api": "/api/v1",
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "api_version": "v1",
    }


@app.get("/health/database")
async def database_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Database health check endpoint."""
    try:
        # Simple database query to test connection
        result = await db.execute("SELECT 1")
        await result.fetchone()
        return {
            "status": "healthy",
            "service": "database",
            "message": "Database connection successful",
        }
    except Exception as e:
        return {"status": "unhealthy", "service": "database", "error": str(e)}


@app.get("/info")
async def app_info() -> Dict[str, Any]:
    """Application information endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "description": "VK Comments monitoring and analysis system",
        "features": [
            "VK API integration",
            "Real-time comment monitoring",
            "Keyword-based filtering",
            "PostgreSQL data storage with full models",
            "Redis caching",
            "Background task processing",
            "RESTful API with FastAPI",
            "Comprehensive monitoring system",
        ],
        "api": {
            "version": "v1",
            "docs": "/docs",
            "endpoints": {
                "health": "/api/v1/health",
                "vk": "/api/v1/vk",
                "monitoring": "/api/v1/monitoring",
            },
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
