"""Monitoring API endpoints."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.monitoring import MonitorStatus
from app.schemas.base import PaginatedResponseSchema, PaginationSchema
from app.schemas.monitoring import (
    CommentMatchResponse,
    CommentMatchWithDetails,
    KeywordCreate,
    KeywordResponse,
    MonitorTaskCreate,
    MonitorTaskResponse,
    MonitorTaskUpdate,
    MonitorTaskWithKeywords,
)
from app.services.monitoring import MonitoringService

router = APIRouter()


@router.get("/tasks", response_model=PaginatedResponseSchema)
async def list_monitor_tasks(
    pagination: PaginationSchema = Depends(),
    status_filter: MonitorStatus = Query(None, description="Filter by status"),
    target_type: str = Query(None, description="Filter by target type"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponseSchema:
    """List monitoring tasks with pagination and filtering."""
    monitoring_service = MonitoringService(db)
    tasks, total = await monitoring_service.get_tasks_paginated(
        offset=pagination.offset,
        limit=pagination.size,
        status=status_filter,
        target_type=target_type,
    )

    return PaginatedResponseSchema.create(
        items=[task.to_dict() for task in tasks],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


@router.get("/tasks/{task_id}", response_model=MonitorTaskWithKeywords)
async def get_monitor_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MonitorTaskWithKeywords:
    """Get monitoring task by ID with keywords."""
    monitoring_service = MonitoringService(db)
    task = await monitoring_service.get_task_by_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitoring task not found"
        )

    return MonitorTaskWithKeywords.model_validate(task)


@router.post("/tasks", response_model=MonitorTaskResponse)
async def create_monitor_task(
    task_data: MonitorTaskCreate,
    db: AsyncSession = Depends(get_db),
) -> MonitorTaskResponse:
    """Create new monitoring task with keywords."""
    monitoring_service = MonitoringService(db)

    # Validate target_type
    valid_types = ["group", "user", "post"]
    if task_data.target_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target_type. Must be one of: {valid_types}",
        )

    task = await monitoring_service.create_task(task_data)
    return MonitorTaskResponse.model_validate(task)


@router.put("/tasks/{task_id}", response_model=MonitorTaskResponse)
async def update_monitor_task(
    task_id: uuid.UUID,
    task_update: MonitorTaskUpdate,
    db: AsyncSession = Depends(get_db),
) -> MonitorTaskResponse:
    """Update monitoring task."""
    monitoring_service = MonitoringService(db)

    task = await monitoring_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitoring task not found"
        )

    updated_task = await monitoring_service.update_task(task_id, task_update)
    return MonitorTaskResponse.model_validate(updated_task)


@router.delete("/tasks/{task_id}")
async def delete_monitor_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete monitoring task."""
    monitoring_service = MonitoringService(db)

    task = await monitoring_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitoring task not found"
        )

    await monitoring_service.delete_task(task_id)
    return {"message": "Monitoring task deleted successfully"}


@router.post("/tasks/{task_id}/start")
async def start_monitor_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MonitorTaskResponse:
    """Start monitoring task."""
    monitoring_service = MonitoringService(db)

    task = await monitoring_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitoring task not found"
        )

    if task.status == MonitorStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Task is already active"
        )

    updated_task = await monitoring_service.start_task(task_id)
    return MonitorTaskResponse.model_validate(updated_task)


@router.post("/tasks/{task_id}/pause")
async def pause_monitor_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MonitorTaskResponse:
    """Pause monitoring task."""
    monitoring_service = MonitoringService(db)

    task = await monitoring_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitoring task not found"
        )

    if task.status != MonitorStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Task is not active"
        )

    updated_task = await monitoring_service.pause_task(task_id)
    return MonitorTaskResponse.model_validate(updated_task)


@router.get("/tasks/{task_id}/keywords", response_model=List[KeywordResponse])
async def list_task_keywords(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[KeywordResponse]:
    """List keywords for a monitoring task."""
    monitoring_service = MonitoringService(db)

    task = await monitoring_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitoring task not found"
        )

    keywords = await monitoring_service.get_task_keywords(task_id)
    return [KeywordResponse.model_validate(keyword) for keyword in keywords]


@router.post("/tasks/{task_id}/keywords", response_model=KeywordResponse)
async def add_task_keyword(
    task_id: uuid.UUID,
    keyword_data: KeywordCreate,
    db: AsyncSession = Depends(get_db),
) -> KeywordResponse:
    """Add keyword to monitoring task."""
    monitoring_service = MonitoringService(db)

    task = await monitoring_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitoring task not found"
        )

    keyword = await monitoring_service.add_keyword(task_id, keyword_data)
    return KeywordResponse.model_validate(keyword)


@router.delete("/keywords/{keyword_id}")
async def delete_keyword(
    keyword_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete keyword."""
    monitoring_service = MonitoringService(db)

    keyword = await monitoring_service.get_keyword_by_id(keyword_id)
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found"
        )

    await monitoring_service.delete_keyword(keyword_id)
    return {"message": "Keyword deleted successfully"}


@router.get("/matches", response_model=PaginatedResponseSchema)
async def list_comment_matches(
    pagination: PaginationSchema = Depends(),
    task_id: uuid.UUID = Query(None, description="Filter by task ID"),
    is_reviewed: bool = Query(None, description="Filter by review status"),
    is_relevant: bool = Query(None, description="Filter by relevance"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponseSchema:
    """List comment matches with pagination and filtering."""
    monitoring_service = MonitoringService(db)
    matches, total = await monitoring_service.get_matches_paginated(
        offset=pagination.offset,
        limit=pagination.size,
        task_id=task_id,
        is_reviewed=is_reviewed,
        is_relevant=is_relevant,
    )

    return PaginatedResponseSchema.create(
        items=[match.to_dict() for match in matches],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


@router.get("/matches/{match_id}", response_model=CommentMatchWithDetails)
async def get_comment_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CommentMatchWithDetails:
    """Get comment match by ID with details."""
    monitoring_service = MonitoringService(db)
    match = await monitoring_service.get_match_by_id(match_id)

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment match not found"
        )

    return CommentMatchWithDetails.model_validate(match)
