"""VK API Integration Tests and Validation."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.vk_client import VKClient, get_vk_client, init_vk_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vk-test", tags=["VK API Testing"])


class VKTestResult(BaseModel):
    """Model for VK API test results."""

    test_name: str
    status: str
    success: bool
    message: str
    execution_time: Optional[float] = None
    data: Optional[Dict] = None
    error: Optional[str] = None


class VKTestSuite(BaseModel):
    """Model for complete VK API test suite results."""

    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    execution_time: float
    results: List[VKTestResult]


@router.get("/ping")
async def ping_vk_test():
    """Simple ping test for VK test endpoints."""
    return {
        "status": "healthy",
        "message": "VK Test API is running",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/validate-token")
async def validate_vk_token() -> VKTestResult:
    """Test VK API token validity."""
    start_time = asyncio.get_event_loop().time()

    try:
        # Test token initialization
        is_valid = await init_vk_client()

        execution_time = asyncio.get_event_loop().time() - start_time

        if is_valid:
            return VKTestResult(
                test_name="VK Token Validation",
                status="success",
                success=True,
                message="VK API token is valid and accessible",
                execution_time=execution_time,
                data={"token_configured": bool(settings.VK_API_TOKEN)},
            )
        else:
            return VKTestResult(
                test_name="VK Token Validation",
                status="failed",
                success=False,
                message="VK API token is invalid or inaccessible",
                execution_time=execution_time,
                error="Token validation failed",
            )

    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return VKTestResult(
            test_name="VK Token Validation",
            status="error",
            success=False,
            message="VK API token validation error",
            execution_time=execution_time,
            error=str(e),
        )


@router.get("/test-group-info/{group_id}")
async def test_group_info(group_id: int) -> VKTestResult:
    """Test VK group information fetching."""
    start_time = asyncio.get_event_loop().time()

    try:
        vk_client = get_vk_client()
        group_data = await vk_client.get_group_info(group_id)

        execution_time = asyncio.get_event_loop().time() - start_time

        if group_data:
            return VKTestResult(
                test_name=f"Group Info Test (ID: {group_id})",
                status="success",
                success=True,
                message=f"Successfully fetched group info for {group_id}",
                execution_time=execution_time,
                data=group_data,
            )
        else:
            return VKTestResult(
                test_name=f"Group Info Test (ID: {group_id})",
                status="failed",
                success=False,
                message=f"Could not fetch group info for {group_id}",
                execution_time=execution_time,
                error="Group not found or access denied",
            )

    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return VKTestResult(
            test_name=f"Group Info Test (ID: {group_id})",
            status="error",
            success=False,
            message=f"Error fetching group info for {group_id}",
            execution_time=execution_time,
            error=str(e),
        )


@router.get("/test-wall-posts/{group_id}")
async def test_wall_posts(group_id: int, count: int = 5) -> VKTestResult:
    """Test VK wall posts fetching."""
    start_time = asyncio.get_event_loop().time()

    try:
        vk_client = get_vk_client()
        posts = await vk_client.get_wall_posts(group_id, count=count)

        execution_time = asyncio.get_event_loop().time() - start_time

        if posts:
            return VKTestResult(
                test_name=f"Wall Posts Test (Group: {group_id})",
                status="success",
                success=True,
                message=f"Successfully fetched {len(posts)} posts from group {group_id}",
                execution_time=execution_time,
                data={
                    "posts_count": len(posts),
                    "first_post_id": posts[0].get("vk_post_id") if posts else None,
                    "sample_post": posts[0] if posts else None,
                },
            )
        else:
            return VKTestResult(
                test_name=f"Wall Posts Test (Group: {group_id})",
                status="failed",
                success=False,
                message=f"No posts found for group {group_id}",
                execution_time=execution_time,
                error="No posts available or access denied",
            )

    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return VKTestResult(
            test_name=f"Wall Posts Test (Group: {group_id})",
            status="error",
            success=False,
            message=f"Error fetching posts for group {group_id}",
            execution_time=execution_time,
            error=str(e),
        )


@router.get("/test-comments/{group_id}/{post_id}")
async def test_post_comments(
    group_id: int, post_id: int, count: int = 10
) -> VKTestResult:
    """Test VK post comments fetching."""
    start_time = asyncio.get_event_loop().time()

    try:
        vk_client = get_vk_client()
        comments = await vk_client.get_post_comments(group_id, post_id, count=count)

        execution_time = asyncio.get_event_loop().time() - start_time

        if comments:
            return VKTestResult(
                test_name=f"Comments Test (Post: {post_id})",
                status="success",
                success=True,
                message=f"Successfully fetched {len(comments)} comments from post {post_id}",
                execution_time=execution_time,
                data={
                    "comments_count": len(comments),
                    "first_comment_id": (
                        comments[0].get("vk_comment_id") if comments else None
                    ),
                    "sample_comment": comments[0] if comments else None,
                },
            )
        else:
            return VKTestResult(
                test_name=f"Comments Test (Post: {post_id})",
                status="warning",
                success=True,
                message=f"No comments found for post {post_id} (this is normal)",
                execution_time=execution_time,
                data={"comments_count": 0},
            )

    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return VKTestResult(
            test_name=f"Comments Test (Post: {post_id})",
            status="error",
            success=False,
            message=f"Error fetching comments for post {post_id}",
            execution_time=execution_time,
            error=str(e),
        )


@router.get("/test-user-info/{user_id}")
async def test_user_info(user_id: int) -> VKTestResult:
    """Test VK user information fetching."""
    start_time = asyncio.get_event_loop().time()

    try:
        vk_client = get_vk_client()
        user_data = await vk_client.get_user_info(user_id)

        execution_time = asyncio.get_event_loop().time() - start_time

        if user_data:
            return VKTestResult(
                test_name=f"User Info Test (ID: {user_id})",
                status="success",
                success=True,
                message=f"Successfully fetched user info for {user_id}",
                execution_time=execution_time,
                data=user_data,
            )
        else:
            return VKTestResult(
                test_name=f"User Info Test (ID: {user_id})",
                status="failed",
                success=False,
                message=f"Could not fetch user info for {user_id}",
                execution_time=execution_time,
                error="User not found or access denied",
            )

    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return VKTestResult(
            test_name=f"User Info Test (ID: {user_id})",
            status="error",
            success=False,
            message=f"Error fetching user info for {user_id}",
            execution_time=execution_time,
            error=str(e),
        )


@router.get("/test-keyword-search/{group_id}")
async def test_keyword_search(
    group_id: int, keywords: str = "тест,комментарий"
) -> VKTestResult:
    """Test VK keyword search functionality."""
    start_time = asyncio.get_event_loop().time()

    try:
        vk_client = get_vk_client()
        keyword_list = [k.strip() for k in keywords.split(",")]

        matching_comments = await vk_client.search_comments_by_keywords(
            group_id, keyword_list, limit=20
        )

        execution_time = asyncio.get_event_loop().time() - start_time

        return VKTestResult(
            test_name=f"Keyword Search Test (Group: {group_id})",
            status="success",
            success=True,
            message=f"Keyword search completed for {len(keyword_list)} keywords",
            execution_time=execution_time,
            data={
                "keywords": keyword_list,
                "matching_comments": len(matching_comments),
                "sample_matches": matching_comments[:3] if matching_comments else [],
            },
        )

    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return VKTestResult(
            test_name=f"Keyword Search Test (Group: {group_id})",
            status="error",
            success=False,
            message=f"Error during keyword search for group {group_id}",
            execution_time=execution_time,
            error=str(e),
        )


@router.get("/test-rate-limiting")
async def test_rate_limiting() -> VKTestResult:
    """Test VK API rate limiting compliance."""
    start_time = asyncio.get_event_loop().time()

    try:
        vk_client = get_vk_client()

        # Test multiple rapid requests
        test_requests = []
        for i in range(5):
            request_start = asyncio.get_event_loop().time()
            await vk_client._rate_limit()  # Test rate limiting
            request_end = asyncio.get_event_loop().time()
            test_requests.append(request_end - request_start)

        execution_time = asyncio.get_event_loop().time() - start_time

        # Check if rate limiting is working (should have delays)
        has_delays = any(delay > 0.1 for delay in test_requests[1:])

        return VKTestResult(
            test_name="Rate Limiting Test",
            status="success",
            success=True,
            message=f"Rate limiting test completed {'with' if has_delays else 'without'} delays",
            execution_time=execution_time,
            data={
                "total_requests": len(test_requests),
                "request_delays": test_requests,
                "has_rate_limiting": has_delays,
                "max_delay": max(test_requests) if test_requests else 0,
            },
        )

    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return VKTestResult(
            test_name="Rate Limiting Test",
            status="error",
            success=False,
            message="Error testing rate limiting",
            execution_time=execution_time,
            error=str(e),
        )


@router.get("/run-full-test-suite/{group_id}")
async def run_full_test_suite(group_id: int) -> VKTestSuite:
    """Run complete VK API integration test suite."""
    suite_start_time = asyncio.get_event_loop().time()

    results = []

    # Test 1: Token validation
    results.append(await validate_vk_token())

    # Test 2: Group info
    results.append(await test_group_info(group_id))

    # Test 3: Wall posts
    posts_result = await test_wall_posts(group_id, count=3)
    results.append(posts_result)

    # Test 4: Comments (if we have posts)
    if (
        posts_result.success
        and posts_result.data
        and posts_result.data.get("first_post_id")
    ):
        first_post_id = posts_result.data["first_post_id"]
        results.append(await test_post_comments(group_id, first_post_id, count=5))

    # Test 5: User info (try with a common user ID)
    results.append(await test_user_info(1))  # Pavel Durov's ID

    # Test 6: Keyword search
    results.append(await test_keyword_search(group_id))

    # Test 7: Rate limiting
    results.append(await test_rate_limiting())

    # Calculate results
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.success)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

    suite_execution_time = asyncio.get_event_loop().time() - suite_start_time

    return VKTestSuite(
        total_tests=total_tests,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        success_rate=success_rate,
        execution_time=suite_execution_time,
        results=results,
    )


@router.get("/test-configuration")
async def test_configuration() -> VKTestResult:
    """Test VK API configuration and settings."""
    start_time = asyncio.get_event_loop().time()

    try:
        config_data = {
            "vk_api_token_configured": bool(settings.VK_API_TOKEN),
            "vk_api_version": settings.VK_API_VERSION,
            "requests_per_second": settings.VK_API_REQUESTS_PER_SECOND,
            "timeout": settings.VK_API_TIMEOUT,
        }

        execution_time = asyncio.get_event_loop().time() - start_time

        return VKTestResult(
            test_name="Configuration Test",
            status="success",
            success=True,
            message="VK API configuration loaded successfully",
            execution_time=execution_time,
            data=config_data,
        )

    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return VKTestResult(
            test_name="Configuration Test",
            status="error",
            success=False,
            message="Error loading VK API configuration",
            execution_time=execution_time,
            error=str(e),
        )
