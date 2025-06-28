"""VK API client for comments monitoring."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from vkbottle import API
from vkbottle.exception import VKAPIError

from app.core.config import settings

logger = logging.getLogger(__name__)


class VKClient:
    """VK API client for fetching comments and posts."""

    def __init__(self, access_token: Optional[str] = None):
        """Initialize VK client."""
        self.access_token = access_token or settings.VK_API_TOKEN
        if not self.access_token:
            raise ValueError("VK API token is required")

        self.api = API(token=self.access_token)
        self.api_version = settings.VK_API_VERSION
        self.requests_per_second = settings.VK_API_REQUESTS_PER_SECOND
        self.timeout = settings.VK_API_TIMEOUT

        # Rate limiting
        self._last_request_time = 0.0
        self._request_interval = 1.0 / self.requests_per_second

    async def _rate_limit(self):
        """Ensure rate limiting compliance."""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self._last_request_time

        if time_since_last < self._request_interval:
            sleep_time = self._request_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self._last_request_time = asyncio.get_event_loop().time()

    async def get_group_info(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get VK group information."""
        try:
            await self._rate_limit()

            result = await self.api.groups.get_by_id(
                group_id=str(group_id),
                fields="name,screen_name,description,members_count,activity",
            )

            if result and len(result) > 0:
                group = result[0]
                return {
                    "vk_group_id": group.id,
                    "name": group.name,
                    "screen_name": getattr(group, "screen_name", None),
                    "description": getattr(group, "description", None),
                    "member_count": getattr(group, "members_count", 0),
                    "activity": getattr(group, "activity", None),
                }

            return None

        except VKAPIError as e:
            logger.error(f"VK API error getting group {group_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting group {group_id}: {e}")
            return None

    async def get_wall_posts(
        self, group_id: int, count: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get wall posts from VK group."""
        try:
            await self._rate_limit()

            result = await self.api.wall.get(
                owner_id=-group_id,  # Negative for groups
                count=min(count, 100),  # VK API limit
                offset=offset,
                extended=1,
                fields="id,date,text,from_id,comments,likes,reposts",
            )

            posts = []
            if result and hasattr(result, "items"):
                for post in result.items:
                    posts.append(
                        {
                            "vk_post_id": post.id,
                            "vk_group_id": group_id,
                            "author_id": getattr(post, "from_id", None),
                            "text": getattr(post, "text", ""),
                            "date": datetime.fromtimestamp(post.date),
                            "likes_count": (
                                getattr(post.likes, "count", 0)
                                if hasattr(post, "likes")
                                else 0
                            ),
                            "comments_count": (
                                getattr(post.comments, "count", 0)
                                if hasattr(post, "comments")
                                else 0
                            ),
                            "reposts_count": (
                                getattr(post.reposts, "count", 0)
                                if hasattr(post, "reposts")
                                else 0
                            ),
                            "post_url": f"https://vk.com/wall-{group_id}_{post.id}",
                        }
                    )

            return posts

        except VKAPIError as e:
            logger.error(f"VK API error getting posts from group {group_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting posts from group {group_id}: {e}")
            return []

    async def get_post_comments(
        self,
        group_id: int,
        post_id: int,
        count: int = 100,
        offset: int = 0,
        sort: str = "desc",
    ) -> List[Dict[str, Any]]:
        """Get comments for a specific post."""
        try:
            await self._rate_limit()

            result = await self.api.wall.get_comments(
                owner_id=-group_id,  # Negative for groups
                post_id=post_id,
                count=min(count, 100),  # VK API limit
                offset=offset,
                sort=sort,
                extended=1,
                fields="id,date,text,from_id",
            )

            comments = []
            if result and hasattr(result, "items"):
                for comment in result.items:
                    # Get author info if available
                    author_name = None
                    author_screen_name = None

                    if hasattr(result, "profiles") and result.profiles:
                        for profile in result.profiles:
                            if profile.id == comment.from_id:
                                author_name = (
                                    f"{profile.first_name} {profile.last_name}"
                                )
                                author_screen_name = getattr(
                                    profile, "screen_name", None
                                )
                                break

                    comments.append(
                        {
                            "vk_comment_id": comment.id,
                            "vk_post_id": post_id,
                            "vk_group_id": group_id,
                            "author_id": comment.from_id,
                            "author_name": author_name,
                            "author_screen_name": author_screen_name,
                            "text": getattr(comment, "text", ""),
                            "date": datetime.fromtimestamp(comment.date),
                            "comment_url": f"https://vk.com/wall-{group_id}_{post_id}?reply={comment.id}",
                        }
                    )

            return comments

        except VKAPIError as e:
            logger.error(f"VK API error getting comments for post {post_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting comments for post {post_id}: {e}")
            return []

    async def search_comments_by_keywords(
        self, group_id: int, keywords: List[str], limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for comments containing specific keywords."""
        all_comments = []

        try:
            # Get recent posts first
            posts = await self.get_wall_posts(group_id, count=20)

            for post in posts:
                post_id = post["vk_post_id"]
                comments = await self.get_post_comments(group_id, post_id, count=100)

                # Filter comments by keywords
                for comment in comments:
                    comment_text = comment.get("text", "").lower()

                    for keyword in keywords:
                        if keyword.lower() in comment_text:
                            comment["matched_keyword"] = keyword
                            comment["post_text"] = post.get("text", "")
                            comment["post_url"] = post.get("post_url", "")
                            all_comments.append(comment)
                            break  # Found match, no need to check other keywords

                # Respect limit
                if len(all_comments) >= limit:
                    break

            return all_comments[:limit]

        except Exception as e:
            logger.error(f"Error searching comments in group {group_id}: {e}")
            return []

    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get VK user information."""
        try:
            await self._rate_limit()

            result = await self.api.users.get(
                user_ids=[user_id],
                fields="screen_name,photo_50,photo_100,verified,followers_count",
            )

            if result and len(result) > 0:
                user = result[0]
                return {
                    "vk_user_id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "screen_name": getattr(user, "screen_name", None),
                    "photo_url": getattr(user, "photo_100", None),
                    "is_verified": getattr(user, "verified", False),
                    "followers_count": getattr(user, "followers_count", 0),
                }

            return None

        except VKAPIError as e:
            logger.error(f"VK API error getting user {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user {user_id}: {e}")
            return None

    async def check_token_validity(self) -> bool:
        """Check if the VK API token is valid."""
        try:
            await self._rate_limit()
            result = await self.api.account.get_info()
            return result is not None
        except VKAPIError:
            return False
        except Exception:
            return False


# Global VK client instance
_vk_client: Optional[VKClient] = None


def get_vk_client() -> VKClient:
    """Get global VK client instance."""
    global _vk_client

    if _vk_client is None:
        if not settings.VK_API_TOKEN:
            raise ValueError("VK API token not configured")
        _vk_client = VKClient(settings.VK_API_TOKEN)

    return _vk_client


async def init_vk_client() -> bool:
    """Initialize and validate VK client."""
    try:
        client = get_vk_client()
        is_valid = await client.check_token_validity()

        if is_valid:
            logger.info("VK API client initialized successfully")
        else:
            logger.error("VK API token is invalid")

        return is_valid

    except Exception as e:
        logger.error(f"Failed to initialize VK client: {e}")
        return False
