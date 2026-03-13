"""API client for ONE Pocket (Edifice)."""

from __future__ import annotations

import re
import time
from datetime import date, timedelta
from typing import Any

import aiohttp

from .const import (
    LOGGER,
    OAUTH_CLIENT_ID,
    OAUTH_CLIENT_SECRET,
    OAUTH_SCOPES,
)


class OnePocketAuthError(Exception):
    """Authentication error."""


class OnePocketApiError(Exception):
    """API error."""


def _strip_html(html: str) -> str:
    """Strip HTML tags from a string."""
    text = re.sub(r"<[^>]+>", "", html)
    text = text.replace("\u200b", "").replace("&nbsp;", " ").replace("&apos;", "'")
    return text.strip()


class OnePocketClient:
    """Client for the ONE Pocket API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        username: str,
        password: str,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: float = 0
        self._user_info: dict[str, Any] | None = None

    async def authenticate(self) -> dict[str, Any]:
        """Authenticate and return user info."""
        await self._get_token()
        self._user_info = await self._get_userinfo()
        return self._user_info

    async def _get_token(self) -> None:
        """Get OAuth2 token."""
        import base64

        credentials = base64.b64encode(
            f"{OAUTH_CLIENT_ID}:{OAUTH_CLIENT_SECRET}".encode()
        ).decode()

        data = {
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
            "client_id": OAUTH_CLIENT_ID,
            "client_secret": OAUTH_CLIENT_SECRET,
            "scope": OAUTH_SCOPES,
        }

        resp = await self._session.post(
            f"{self._base_url}/auth/oauth2/token",
            data=data,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        result = await resp.json(content_type=None)

        if "access_token" not in result:
            error = result.get("error_description", result.get("error", "Unknown"))
            raise OnePocketAuthError(f"Authentication failed: {error}")

        self._access_token = result["access_token"]
        self._refresh_token = result.get("refresh_token")
        expires_in = result.get("expires_in", 3600)
        self._token_expires_at = time.monotonic() + int(expires_in)
        LOGGER.debug("Token acquired, expires in %s seconds", expires_in)

    async def _refresh_access_token(self) -> None:
        """Refresh the access token."""
        if not self._refresh_token:
            await self._get_token()
            return

        import base64

        credentials = base64.b64encode(
            f"{OAUTH_CLIENT_ID}:{OAUTH_CLIENT_SECRET}".encode()
        ).decode()

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": OAUTH_CLIENT_ID,
            "client_secret": OAUTH_CLIENT_SECRET,
            "scope": OAUTH_SCOPES,
        }

        resp = await self._session.post(
            f"{self._base_url}/auth/oauth2/token",
            data=data,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        result = await resp.json(content_type=None)

        if "access_token" not in result:
            # Refresh failed, re-authenticate with password
            LOGGER.debug("Refresh token failed, falling back to password grant")
            await self._get_token()
            return

        self._access_token = result["access_token"]
        self._refresh_token = result.get("refresh_token", self._refresh_token)
        expires_in = result.get("expires_in", 3600)
        self._token_expires_at = time.monotonic() + int(expires_in)
        LOGGER.debug("Token refreshed, expires in %s seconds", expires_in)

    async def _ensure_token(self) -> None:
        """Ensure we have a valid token, refreshing proactively if needed."""
        if not self._access_token:
            await self._get_token()
            return

        remaining = self._token_expires_at - time.monotonic()
        if remaining < 720:  # Less than 12 min left (20% of 1h token)
            LOGGER.debug(
                "Token expires in %.0f seconds, proactively refreshing",
                max(remaining, 0),
            )
            await self._refresh_access_token()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make an authenticated API request."""
        await self._ensure_token()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._access_token}"

        resp = await self._session.request(
            method,
            f"{self._base_url}{path}",
            headers=headers,
            allow_redirects=False,
            **kwargs,
        )

        # ENTCore may redirect to login page instead of returning 401
        if resp.status in (301, 302):
            location = resp.headers.get("Location", "")
            if "/auth/login" in location:
                LOGGER.debug("Redirected to login page, refreshing token")
                await self._refresh_access_token()
                headers["Authorization"] = f"Bearer {self._access_token}"
                resp = await self._session.request(
                    method,
                    f"{self._base_url}{path}",
                    headers=headers,
                    allow_redirects=False,
                    **kwargs,
                )

        if resp.status == 401:
            # Token expired, refresh and retry
            LOGGER.debug("Got 401, refreshing token")
            await self._refresh_access_token()
            headers["Authorization"] = f"Bearer {self._access_token}"
            resp = await self._session.request(
                method,
                f"{self._base_url}{path}",
                headers=headers,
                allow_redirects=False,
                **kwargs,
            )

        if resp.status >= 400:
            text = await resp.text()
            raise OnePocketApiError(
                f"API error {resp.status} on {path}: {text[:200]}"
            )

        # Some endpoints return empty body
        if resp.content_length == 0:
            return {}

        return await resp.json(content_type=None)

    async def _get_userinfo(self) -> dict[str, Any]:
        """Get user info."""
        return await self._request(
            "GET",
            "/auth/oauth2/userinfo",
            headers={"Accept": "application/json;version=2.0"},
        )

    def get_children(self) -> dict[str, str]:
        """Get children dict {id: name} from cached user info."""
        if not self._user_info:
            return {}
        children = self._user_info.get("children", {})
        return {
            child_id: f"{info['firstName']} {info['lastName']}"
            for child_id, info in children.items()
        }

    def get_structures(self) -> list[str]:
        """Get structure IDs from cached user info."""
        if not self._user_info:
            return []
        return self._user_info.get("structures", [])

    async def get_unread_count(self) -> int:
        """Get unread message count."""
        result = await self._request(
            "GET", "/conversation/count/INBOX?unread=true"
        )
        return result.get("count", 0)

    async def get_messages(self, page: int = 0, page_size: int = 10) -> list[dict]:
        """Get inbox messages."""
        messages = await self._request(
            "GET",
            f"/conversation/list/INBOX?page={page}&page_size={page_size}",
        )
        result = []
        for msg in messages:
            # Resolve sender name from displayNames
            sender = msg.get("from", "")
            display_names = {dn[0]: dn[1] for dn in msg.get("displayNames", [])}
            sender_name = display_names.get(sender, sender)

            result.append({
                "id": msg.get("id"),
                "subject": msg.get("subject", ""),
                "from": sender_name,
                "date": msg.get("date", ""),
                "unread": msg.get("unread", False),
            })
        return result

    async def get_homeworks(self, diary_id: str) -> list[dict]:
        """Get homework entries from a diary."""
        result = await self._request("GET", f"/homeworks/get/{diary_id}")
        entries = []
        today = date.today()
        # Only return entries from the last 7 days and next 14 days
        start = today - timedelta(days=7)
        end = today + timedelta(days=14)

        for day in result.get("data", []):
            day_date = day.get("date", "")
            try:
                d = date.fromisoformat(day_date)
            except (ValueError, TypeError):
                continue
            if start <= d <= end:
                for entry in day.get("entries", []):
                    entries.append({
                        "date": day_date,
                        "title": entry.get("title", ""),
                        "content": _strip_html(entry.get("value", "")),
                        "id": entry.get("_id", ""),
                    })
        return entries

    async def get_homework_diaries(self) -> list[dict]:
        """Get list of homework diaries."""
        result = await self._request("GET", "/homeworks/list")
        return [
            {
                "id": d.get("_id", ""),
                "name": d.get("name", ""),
                "owner": d.get("owner", {}).get("displayName", ""),
            }
            for d in result
        ]

    async def get_news(self, page: int = 0, page_size: int = 10) -> list[dict]:
        """Get news/actualites."""
        result = await self._request(
            "GET",
            f"/actualites/list?page={page}&pageSize={page_size}",
        )
        return [
            {
                "id": item.get("id"),
                "title": item.get("title", ""),
                "content": _strip_html(item.get("content", "")),
                "date": item.get("created", ""),
                "author": item.get("owner", {}).get("displayName", ""),
                "comments": item.get("numberOfComments", 0),
            }
            for item in result
        ]

    async def get_blog_posts(self, limit: int = 10) -> list[dict]:
        """Get recent blog posts across all blogs."""
        blogs = await self._request("GET", "/blog/list/all")
        posts = []
        for blog in blogs[:5]:  # Limit to 5 blogs
            blog_id = blog.get("_id", "")
            blog_title = blog.get("title", "")
            try:
                blog_posts = await self._request(
                    "GET",
                    f"/blog/post/list/all/{blog_id}?content=true&page=0&states=PUBLISHED",
                )
                for post in blog_posts[:3]:  # Latest 3 per blog
                    posts.append({
                        "id": post.get("_id", ""),
                        "blog": blog_title,
                        "title": post.get("title", ""),
                        "content": _strip_html(post.get("content", ""))[:300],
                        "date": post.get("created", {}).get("$date", ""),
                        "author": post.get("author", {}).get("username", ""),
                    })
            except OnePocketApiError:
                LOGGER.debug("Could not fetch posts for blog %s", blog_id)
        # Sort by date descending
        posts.sort(key=lambda p: p.get("date", ""), reverse=True)
        return posts[:limit]

    async def get_schoolbook(self, page: int = 0) -> list[dict]:
        """Get schoolbook (carnet de liaison) entries."""
        try:
            result = await self._request("GET", f"/schoolbook/list/{page}")
            if not isinstance(result, list):
                return []
            return [
                {
                    "id": item.get("id"),
                    "title": item.get("title", ""),
                    "content": _strip_html(item.get("content", "")),
                    "date": item.get("created", ""),
                    "author": item.get("owner", {}).get("displayName", ""),
                }
                for item in result
            ]
        except OnePocketApiError:
            return []

    async def get_timeline(self, page: int = 0) -> list[dict]:
        """Get timeline notifications."""
        result = await self._request(
            "GET",
            f"/timeline/lastNotifications?page={page}",
            headers={"Accept": "application/json;version=3.0"},
        )
        notifications = result.get("results", [])
        return [
            {
                "id": n.get("_id", ""),
                "type": n.get("type", ""),
                "event": n.get("event-type", ""),
                "message": _strip_html(n.get("message", "")),
                "date": n.get("date", {}).get("$date", ""),
            }
            for n in notifications[:20]
        ]
