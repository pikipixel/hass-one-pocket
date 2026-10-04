"""The ONE Pocket integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import (
    ConfigEntryNotReady,
    HomeAssistantError,
    ServiceValidationError,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OnePocketApiError, OnePocketAuthError, OnePocketClient
from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_MESSAGE_IDS,
    ATTR_UNREAD,
    CONF_BASE_URL,
    DEFAULT_BASE_URL,
    DOMAIN,
    LOGGER,
    SERVICE_MARK_MESSAGES_READ,
)
from .coordinator import OnePocketCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

MARK_MESSAGES_READ_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MESSAGE_IDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_UNREAD, default=False): cv.boolean,
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)


def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services (once, shared by all config entries)."""
    if hass.services.has_service(DOMAIN, SERVICE_MARK_MESSAGES_READ):
        return

    async def _async_mark_messages_read(call: ServiceCall) -> None:
        """Mark inbox messages as read (or unread) in ONE."""
        coordinators: dict[str, OnePocketCoordinator] = hass.data.get(DOMAIN, {})
        entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        if entry_id is not None:
            if entry_id not in coordinators:
                raise ServiceValidationError(
                    f"Unknown ONE Pocket config entry: {entry_id}"
                )
            targets = [coordinators[entry_id]]
        else:
            # Several children of the same parent account share one inbox:
            # call the API once per distinct account.
            seen: set[tuple[str, str]] = set()
            targets = []
            for coordinator in coordinators.values():
                entry = coordinator.config_entry
                account = (
                    entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
                    entry.data[CONF_USERNAME],
                )
                if account not in seen:
                    seen.add(account)
                    targets.append(coordinator)
        if not targets:
            raise ServiceValidationError("No ONE Pocket account is configured")

        for coordinator in targets:
            try:
                await coordinator.client.set_messages_unread(
                    call.data[ATTR_MESSAGE_IDS], call.data[ATTR_UNREAD]
                )
            except (OnePocketApiError, OnePocketAuthError, TimeoutError) as err:
                raise HomeAssistantError(
                    f"Failed to update messages in ONE: {err}"
                ) from err

        # Refresh every entry so all sensors reflect the new state.
        for coordinator in coordinators.values():
            await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_MARK_MESSAGES_READ,
        _async_mark_messages_read,
        schema=MARK_MESSAGES_READ_SCHEMA,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ONE Pocket from a config entry."""
    session = async_get_clientsession(hass)
    client = OnePocketClient(
        session=session,
        base_url=entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )

    try:
        await client.authenticate()
    except OnePocketAuthError as err:
        raise ConfigEntryNotReady(
            f"Authentication failed, will retry: {err}"
        ) from err
    except (OnePocketApiError, TimeoutError) as err:
        raise ConfigEntryNotReady(
            f"Cannot connect to ONE Pocket, will retry: {err}"
        ) from err

    coordinator = OnePocketCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_register_services(hass)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_MARK_MESSAGES_READ)
    return unload_ok
