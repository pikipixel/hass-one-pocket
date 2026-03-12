"""Sensor platform for ONE Pocket."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CHILD_NAME, DOMAIN
from .coordinator import OnePocketCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ONE Pocket sensors from a config entry."""
    coordinator: OnePocketCoordinator = hass.data[DOMAIN][entry.entry_id]
    child_name = entry.data.get(CONF_CHILD_NAME, entry.title)

    sensors: list[SensorEntity] = [
        OnePocketUnreadSensor(coordinator, entry, child_name),
        OnePocketHomeworkSensor(coordinator, entry, child_name),
        OnePocketNewsSensor(coordinator, entry, child_name),
        OnePocketBlogSensor(coordinator, entry, child_name),
        OnePocketSchoolbookSensor(coordinator, entry, child_name),
        OnePocketTimelineSensor(coordinator, entry, child_name),
    ]

    async_add_entities(sensors)


class OnePocketBaseSensor(CoordinatorEntity[OnePocketCoordinator], SensorEntity):
    """Base sensor for ONE Pocket."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OnePocketCoordinator,
        entry: ConfigEntry,
        child_name: str,
        sensor_key: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_key = sensor_key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{sensor_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"ONE Pocket - {child_name}",
            manufacturer="Edifice",
            model="ONE Pocket",
            entry_type=DeviceEntryType.SERVICE,
        )


class OnePocketUnreadSensor(OnePocketBaseSensor):
    """Sensor for unread message count."""

    def __init__(
        self,
        coordinator: OnePocketCoordinator,
        entry: ConfigEntry,
        child_name: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            coordinator, entry, child_name,
            "unread_messages", "Messages non lus", "mdi:email-outline",
        )

    @property
    def native_value(self) -> int:
        """Return the unread count."""
        return self.coordinator.data.get("unread_messages", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return recent messages as attributes."""
        messages = self.coordinator.data.get("messages", [])
        return {
            "messages": messages[:5],
        }


class OnePocketHomeworkSensor(OnePocketBaseSensor):
    """Sensor for homework."""

    def __init__(
        self,
        coordinator: OnePocketCoordinator,
        entry: ConfigEntry,
        child_name: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            coordinator, entry, child_name,
            "homework", "Devoirs", "mdi:book-open-variant",
        )

    @property
    def native_value(self) -> int:
        """Return the number of homework entries."""
        return len(self.coordinator.data.get("homeworks", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return homework entries as attributes."""
        return {
            "entries": self.coordinator.data.get("homeworks", []),
        }


class OnePocketNewsSensor(OnePocketBaseSensor):
    """Sensor for school news."""

    def __init__(
        self,
        coordinator: OnePocketCoordinator,
        entry: ConfigEntry,
        child_name: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            coordinator, entry, child_name,
            "news", "Actualites", "mdi:newspaper-variant",
        )

    @property
    def native_value(self) -> int:
        """Return the number of news items."""
        return len(self.coordinator.data.get("news", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return news items as attributes."""
        return {
            "items": self.coordinator.data.get("news", []),
        }


class OnePocketBlogSensor(OnePocketBaseSensor):
    """Sensor for blog posts."""

    def __init__(
        self,
        coordinator: OnePocketCoordinator,
        entry: ConfigEntry,
        child_name: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            coordinator, entry, child_name,
            "blog", "Blog", "mdi:post-outline",
        )

    @property
    def native_value(self) -> int:
        """Return the number of blog posts."""
        return len(self.coordinator.data.get("blog_posts", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return blog posts as attributes."""
        return {
            "posts": self.coordinator.data.get("blog_posts", []),
        }


class OnePocketSchoolbookSensor(OnePocketBaseSensor):
    """Sensor for carnet de liaison."""

    def __init__(
        self,
        coordinator: OnePocketCoordinator,
        entry: ConfigEntry,
        child_name: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            coordinator, entry, child_name,
            "schoolbook", "Carnet de liaison", "mdi:notebook-outline",
        )

    @property
    def native_value(self) -> int:
        """Return the number of schoolbook entries."""
        return len(self.coordinator.data.get("schoolbook", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return schoolbook entries as attributes."""
        return {
            "entries": self.coordinator.data.get("schoolbook", []),
        }


class OnePocketTimelineSensor(OnePocketBaseSensor):
    """Sensor for timeline/notifications."""

    def __init__(
        self,
        coordinator: OnePocketCoordinator,
        entry: ConfigEntry,
        child_name: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            coordinator, entry, child_name,
            "timeline", "Notifications", "mdi:bell-outline",
        )

    @property
    def native_value(self) -> int:
        """Return the number of notifications."""
        return len(self.coordinator.data.get("timeline", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return timeline notifications as attributes."""
        return {
            "notifications": self.coordinator.data.get("timeline", []),
        }
