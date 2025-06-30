"""
VK API Client with rate limiting and comprehensive error handling.

This module provides a robust VK API client specifically designed for 
comment monitoring and group analysis.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class VKAPIError(Exception):
    """Base VK API error."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        super().__init__(message)
        self.error_code = error_code


class VKRateLimitError(VKAPIError):
    """VK API rate limit exceeded."""

    pass


class VKResponse(BaseModel):
    """VK API response model."""

    response: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class VKComment(BaseModel):
    """VK Comment model."""

    id: int
    post_id: int
    from_id: int
    text: str
    date: int
    reply_to_user: Optional[int] = None
    reply_to_comment: Optional[int] = None


class VKPost(BaseModel):
    """VK Post model."""

    id: int
    owner_id: int
    from_id: Optional[int] = None
    date: int
    text: str
    comments_count: Optional[int] = 0
    likes_count: Optional[int] = 0
    reposts_count: Optional[int] = 0


class VKGroup(BaseModel):
    """VK Group model."""

    id: int
    name: str
    screen_name: str
    type: str
    description: Optional[str] = None
    members_count: Optional[int] = 0
    photo_200: Optional[str] = None


class VKAPIClient:
    """
    Asynchronous VK API client with built-in rate limiting and error handling.

    Features:
    - Automatic rate limiting (3 requests/second by default)
    - Retry logic with exponential backoff
    - Comprehensive error handling
    - Request/response logging
    - Connection pooling
    """

    def __init__(
        self,
        access_token: str,
        api_version: str = "5.131",
        requests_per_second: int = 3,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        self.access_token = access_token
        self.api_version = api_version
        self.requests_per_second = requests_per_second
        self.max_retries = max_retries
        self.timeout = timeout

        # Rate limiting
        self._last_request_time = 0.0
        self._request_interval = 1.0 / requests_per_second

        # HTTP session
        self._session: Optional[aiohttp.ClientSession] = None

        # Base URL
        self._base_url = "https://api.vk.com/method"

        logger.info(
            f"VK API Client initialized: version={api_version}, "
            f"rate_limit={requests_per_second}/sec"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure HTTP session is created."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=10,
                keepalive_timeout=30,
            )

            timeout = aiohttp.ClientTimeout(total=self.timeout)

            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": "VK-Comments-Monitor/1.0",
                },
            )

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _rate_limit(self):
        """Apply rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._request_interval:
            sleep_time = self._request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

        self._last_request_time = time.time()

    async def _make_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a single API request with rate limiting and error handling.

        Args:
            method: VK API method name
            params: Request parameters

        Returns:
            API response data

        Raises:
            VKAPIError: On API errors
            VKRateLimitError: On rate limit exceeded
        """
        await self._ensure_session()
        await self._rate_limit()

        # Prepare parameters
        request_params = {
            "access_token": self.access_token,
            "v": self.api_version,
        }

        if params:
            request_params.update(params)

        url = f"{self._base_url}/{method}"

        logger.debug(f"VK API request: {method} with {len(request_params)} params")

        try:
            async with self._session.get(url, params=request_params) as response:
                response.raise_for_status()
                data = await response.json()

                # Check for VK API errors
                if "error" in data:
                    error = data["error"]
                    error_code = error.get("error_code")
                    error_msg = error.get("error_msg", "Unknown VK API error")

                    logger.error(f"VK API error {error_code}: {error_msg}")

                    # Handle specific error codes
                    if error_code == 6:  # Too many requests per second
                        raise VKRateLimitError(f"Rate limit exceeded: {error_msg}")
                    elif error_code in [5, 15]:  # Access denied or blocked
                        raise VKAPIError(f"Access denied: {error_msg}", error_code)
                    else:
                        raise VKAPIError(f"VK API error: {error_msg}", error_code)

                logger.debug(f"VK API response: {method} successful")
                return data.get("response", {})

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error for {method}: {e}")
            raise VKAPIError(f"HTTP request failed: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout for {method}")
            raise VKAPIError(f"Request timeout for {method}")

    async def _make_request_with_retry(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make request with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await self._make_request(method, params)

            except VKRateLimitError:
                # Rate limit errors should wait longer
                if attempt < self.max_retries:
                    wait_time = 2**attempt
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)
                    continue
                raise

            except VKAPIError as e:
                last_exception = e
                if e.error_code in [5, 15]:  # Don't retry access errors
                    raise

                if attempt < self.max_retries:
                    wait_time = 1.5**attempt
                    logger.warning(
                        f"API error on attempt {attempt + 1}, retrying in {wait_time:.1f}s"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = 2**attempt
                    logger.warning(
                        f"Unexpected error on attempt {attempt + 1}, retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise VKAPIError(f"Max retries exceeded: {e}")

        if last_exception:
            raise last_exception

    async def get_group_info(self, group_id: int) -> VKGroup:
        """
        Get group information by ID.

        Args:
            group_id: VK group ID (positive number)

        Returns:
            VKGroup model with group information
        """
        logger.info(f"Getting group info for ID: {group_id}")

        params = {
            "group_ids": str(group_id),
            "fields": "description,members_count,photo_200",
        }

        try:
            response = await self._make_request_with_retry("groups.getById", params)

            if not response or not isinstance(response, list) or len(response) == 0:
                raise VKAPIError(f"Group {group_id} not found")

            group_data = response[0]

            return VKGroup(
                id=group_data["id"],
                name=group_data["name"],
                screen_name=group_data["screen_name"],
                type=group_data["type"],
                description=group_data.get("description"),
                members_count=group_data.get("members_count"),
                photo_200=group_data.get("photo_200"),
            )

        except Exception as e:
            logger.error(f"Failed to get group info for {group_id}: {e}")
            raise

    async def get_wall_posts(
        self,
        group_id: int,
        count: int = 20,
        offset: int = 0,
        filter: str = "owner",
    ) -> List[VKPost]:
        """
        Get wall posts from a group.

        Args:
            group_id: VK group ID
            count: Number of posts to retrieve (max 100)
            offset: Offset for pagination
            filter: Post filter ("owner", "others", "all")

        Returns:
            List of VKPost models
        """
        logger.info(f"Getting {count} posts from group {group_id} (offset={offset})")

        params = {
            "owner_id": f"-{group_id}",
            "count": min(count, 100),
            "offset": offset,
            "filter": filter,
            "extended": 1,
        }

        try:
            response = await self._make_request_with_retry("wall.get", params)

            posts = []
            for post_data in response.get("items", []):
                # Skip ads and deleted posts
                if post_data.get("marked_as_ads") or "text" not in post_data:
                    continue

                post = VKPost(
                    id=post_data["id"],
                    owner_id=post_data["owner_id"],
                    from_id=post_data.get("from_id"),
                    date=post_data["date"],
                    text=post_data["text"],
                    comments_count=post_data.get("comments", {}).get("count", 0),
                    likes_count=post_data.get("likes", {}).get("count", 0),
                    reposts_count=post_data.get("reposts", {}).get("count", 0),
                )
                posts.append(post)

            logger.info(f"Retrieved {len(posts)} posts from group {group_id}")
            return posts

        except Exception as e:
            logger.error(f"Failed to get posts for group {group_id}: {e}")
            raise

    async def get_post_comments(
        self,
        group_id: int,
        post_id: int,
        count: int = 100,
        offset: int = 0,
        sort: str = "asc",
    ) -> List[VKComment]:
        """
        Get comments for a specific post.

        Args:
            group_id: VK group ID
            post_id: Post ID
            count: Number of comments to retrieve (max 100)
            offset: Offset for pagination
            sort: Sorting order ("asc" or "desc")

        Returns:
            List of VKComment models
        """
        logger.debug(f"Getting {count} comments for post {post_id} in group {group_id}")

        params = {
            "owner_id": f"-{group_id}",
            "post_id": post_id,
            "count": min(count, 100),
            "offset": offset,
            "sort": sort,
            "need_likes": 1,
        }

        try:
            response = await self._make_request_with_retry("wall.getComments", params)

            comments = []
            for comment_data in response.get("items", []):
                # Skip deleted comments
                if comment_data.get("deleted"):
                    continue

                comment = VKComment(
                    id=comment_data["id"],
                    post_id=post_id,
                    from_id=comment_data["from_id"],
                    text=comment_data["text"],
                    date=comment_data["date"],
                    reply_to_user=comment_data.get("reply_to_user"),
                    reply_to_comment=comment_data.get("reply_to_comment"),
                )
                comments.append(comment)

            logger.debug(f"Retrieved {len(comments)} comments for post {post_id}")
            return comments

        except Exception as e:
            logger.error(f"Failed to get comments for post {post_id}: {e}")
            raise

    async def search_comments_in_group(
        self,
        group_id: int,
        keywords: List[str],
        max_posts: int = 20,
        max_comments_per_post: int = 100,
    ) -> Tuple[List[VKComment], Dict[str, Any]]:
        """
        Search for comments containing specific keywords in a group.

        Args:
            group_id: VK group ID
            keywords: List of keywords to search for
            max_posts: Maximum number of posts to check
            max_comments_per_post: Maximum comments per post to analyze

        Returns:
            Tuple of (matching_comments, search_stats)
        """
        logger.info(f"Searching for keywords {keywords} in group {group_id}")

        # Normalize keywords for case-insensitive search
        normalized_keywords = [kw.lower().strip() for kw in keywords]

        stats = {
            "posts_checked": 0,
            "comments_checked": 0,
            "matches_found": 0,
            "keywords_matched": set(),
        }

        matching_comments = []

        try:
            # Get recent posts from the group
            posts = await self.get_wall_posts(group_id, count=max_posts)

            for post in posts:
                stats["posts_checked"] += 1

                # Get comments for this post
                comments = await self.get_post_comments(
                    group_id, post.id, count=max_comments_per_post
                )

                stats["comments_checked"] += len(comments)

                # Search for keywords in comments
                for comment in comments:
                    comment_text_lower = comment.text.lower()

                    # Check if any keyword matches
                    matched_keywords = [
                        kw for kw in normalized_keywords if kw in comment_text_lower
                    ]

                    if matched_keywords:
                        matching_comments.append(comment)
                        stats["matches_found"] += 1
                        stats["keywords_matched"].update(matched_keywords)

                        logger.debug(
                            f"Found match in comment {comment.id}: "
                            f"keywords={matched_keywords}"
                        )

            # Convert set to list for JSON serialization
            stats["keywords_matched"] = list(stats["keywords_matched"])

            logger.info(
                f"Search completed: {stats['matches_found']} matches found "
                f"in {stats['comments_checked']} comments from {stats['posts_checked']} posts"
            )

            return matching_comments, stats

        except Exception as e:
            logger.error(f"Search failed for group {group_id}: {e}")
            raise
