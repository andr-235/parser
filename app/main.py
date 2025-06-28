"""FastAPI application main module."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.database import close_db, init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting VK Comments Monitor application")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="VK Comments Monitoring System with real VK API integration",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "path": str(request.url.path),
        },
    )


# Include API routes
app.include_router(api_v1_router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with application info."""
    return {
        "message": "VK Comments Monitor API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running",
    }
