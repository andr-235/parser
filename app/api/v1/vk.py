"""VK-related API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.base import PaginatedResponseSchema, PaginationSchema
from app.schemas.vk import (
    VKCommentCreate,
    VKCommentResponse,
    VKCommentWithAuthor,
    VKPostCreate,
    VKPostResponse,
    VKUserCreate,
    VKUserResponse,
)
from app.services.vk import VKService

router = APIRouter()


@router.get("/users", response_model=PaginatedResponseSchema)
async def list_vk_users(
    pagination: PaginationSchema = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponseSchema:
    """List VK users with pagination."""
    vk_service = VKService(db)
    users, total = await vk_service.get_users_paginated(
        offset=pagination.offset, limit=pagination.size
    )

    return PaginatedResponseSchema.create(
        items=[user.to_dict() for user in users],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


@router.get("/users/{user_id}", response_model=VKUserResponse)
async def get_vk_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> VKUserResponse:
    """Get VK user by ID."""
    vk_service = VKService(db)
    user = await vk_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VK user not found"
        )

    return VKUserResponse.model_validate(user)


@router.get("/users/vk/{vk_id}", response_model=VKUserResponse)
async def get_vk_user_by_vk_id(
    vk_id: int,
    db: AsyncSession = Depends(get_db),
) -> VKUserResponse:
    """Get VK user by VK ID."""
    vk_service = VKService(db)
    user = await vk_service.get_user_by_vk_id(vk_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VK user with vk_id={vk_id} not found",
        )

    return VKUserResponse.model_validate(user)


@router.post("/users", response_model=VKUserResponse)
async def create_vk_user(
    user_data: VKUserCreate,
    db: AsyncSession = Depends(get_db),
) -> VKUserResponse:
    """Create new VK user."""
    vk_service = VKService(db)

    # Check if user with this vk_id already exists
    existing_user = await vk_service.get_user_by_vk_id(user_data.vk_id)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with vk_id={user_data.vk_id} already exists",
        )

    user = await vk_service.create_user(user_data)
    return VKUserResponse.model_validate(user)


@router.get("/posts", response_model=PaginatedResponseSchema)
async def list_vk_posts(
    pagination: PaginationSchema = Depends(),
    owner_id: int = Query(None, description="Filter by owner ID"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponseSchema:
    """List VK posts with pagination and filtering."""
    vk_service = VKService(db)
    posts, total = await vk_service.get_posts_paginated(
        offset=pagination.offset, limit=pagination.size, owner_id=owner_id
    )

    return PaginatedResponseSchema.create(
        items=[post.to_dict() for post in posts],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


@router.get("/posts/{post_id}", response_model=VKPostResponse)
async def get_vk_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> VKPostResponse:
    """Get VK post by ID."""
    vk_service = VKService(db)
    post = await vk_service.get_post_by_id(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VK post not found"
        )

    return VKPostResponse.model_validate(post)


@router.post("/posts", response_model=VKPostResponse)
async def create_vk_post(
    post_data: VKPostCreate,
    db: AsyncSession = Depends(get_db),
) -> VKPostResponse:
    """Create new VK post."""
    vk_service = VKService(db)

    # Check if post with this vk_id already exists
    existing_post = await vk_service.get_post_by_vk_id(post_data.vk_id)
    if existing_post:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Post with vk_id={post_data.vk_id} already exists",
        )

    post = await vk_service.create_post(post_data)
    return VKPostResponse.model_validate(post)


@router.get("/comments", response_model=PaginatedResponseSchema)
async def list_vk_comments(
    pagination: PaginationSchema = Depends(),
    post_id: int = Query(None, description="Filter by post VK ID"),
    author_id: int = Query(None, description="Filter by author VK ID"),
    contains_keywords: bool = Query(None, description="Filter by keyword matches"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponseSchema:
    """List VK comments with pagination and filtering."""
    vk_service = VKService(db)
    comments, total = await vk_service.get_comments_paginated(
        offset=pagination.offset,
        limit=pagination.size,
        post_vk_id=post_id,
        author_vk_id=author_id,
        contains_keywords=contains_keywords,
    )

    return PaginatedResponseSchema.create(
        items=[comment.to_dict() for comment in comments],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


@router.get("/comments/{comment_id}", response_model=VKCommentWithAuthor)
async def get_vk_comment(
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> VKCommentWithAuthor:
    """Get VK comment by ID with author information."""
    vk_service = VKService(db)
    comment = await vk_service.get_comment_by_id(comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VK comment not found"
        )

    return VKCommentWithAuthor.model_validate(comment)


@router.post("/comments", response_model=VKCommentResponse)
async def create_vk_comment(
    comment_data: VKCommentCreate,
    db: AsyncSession = Depends(get_db),
) -> VKCommentResponse:
    """Create new VK comment."""
    vk_service = VKService(db)

    # Check if comment with this vk_id already exists
    existing_comment = await vk_service.get_comment_by_vk_id(comment_data.vk_id)
    if existing_comment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Comment with vk_id={comment_data.vk_id} already exists",
        )

    comment = await vk_service.create_comment(comment_data)
    return VKCommentResponse.model_validate(comment)
