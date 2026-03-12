"""Data update coordinator for ONE Pocket."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OnePocketApiError, OnePocketAuthError, OnePocketClient
from .const import CONF_CHILD_NAME, DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER


class OnePocketCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from ONE Pocket."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: OnePocketClient,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self._child_name = config_entry.data.get(CONF_CHILD_NAME, "")
        self._diary_ids: list[str] = []

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=config_entry.options.get(
                    "scan_interval", DEFAULT_SCAN_INTERVAL
                )
            ),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from ONE Pocket API."""
        data: dict[str, Any] = {
            "unread_messages": 0,
            "messages": [],
            "homeworks": [],
            "news": [],
            "blog_posts": [],
            "schoolbook": [],
            "timeline": [],
        }

        try:
            # Re-authenticate if needed (token may have expired between updates)
            try:
                await self.client.authenticate()
            except OnePocketApiError as err:
                LOGGER.warning("Re-authentication failed, using existing token: %s", err)

            # Fetch all data types, each in its own try/except
            # so one failure doesn't prevent other data from loading
            try:
                data["unread_messages"] = await self.client.get_unread_count()
            except OnePocketApiError as err:
                LOGGER.warning("Failed to fetch unread count: %s", err)

            try:
                data["messages"] = await self.client.get_messages(page_size=10)
            except OnePocketApiError as err:
                LOGGER.warning("Failed to fetch messages: %s", err)

            try:
                # Discover homework diaries on first run
                if not self._diary_ids:
                    diaries = await self.client.get_homework_diaries()
                    self._diary_ids = [d["id"] for d in diaries]

                all_hw = []
                for diary_id in self._diary_ids:
                    entries = await self.client.get_homeworks(diary_id)
                    all_hw.extend(entries)
                # Sort by date
                all_hw.sort(key=lambda e: e.get("date", ""))
                data["homeworks"] = all_hw
            except OnePocketApiError as err:
                LOGGER.warning("Failed to fetch homeworks: %s", err)

            try:
                data["news"] = await self.client.get_news(page_size=10)
            except OnePocketApiError as err:
                LOGGER.warning("Failed to fetch news: %s", err)

            try:
                data["blog_posts"] = await self.client.get_blog_posts(limit=10)
            except OnePocketApiError as err:
                LOGGER.warning("Failed to fetch blog posts: %s", err)

            try:
                data["schoolbook"] = await self.client.get_schoolbook()
            except OnePocketApiError as err:
                LOGGER.warning("Failed to fetch schoolbook: %s", err)

            try:
                data["timeline"] = await self.client.get_timeline()
            except OnePocketApiError as err:
                LOGGER.warning("Failed to fetch timeline: %s", err)

        except OnePocketAuthError as err:
            raise ConfigEntryAuthFailed from err
        except OnePocketApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

        return data
