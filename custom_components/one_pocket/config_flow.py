"""Config flow for ONE Pocket integration."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OnePocketAuthError, OnePocketClient
from .const import (
    CONF_BASE_URL,
    CONF_CHILD_ID,
    CONF_CHILD_NAME,
    CONF_STRUCTURE_ID,
    DEFAULT_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class OnePocketConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ONE Pocket."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_input: dict[str, Any] = {}
        self._children: dict[str, str] = {}
        self._structures: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the credentials step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = OnePocketClient(
                session=session,
                base_url=user_input[CONF_BASE_URL],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
            )

            try:
                await client.authenticate()
            except OnePocketAuthError:
                errors["base"] = "invalid_auth"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                self._user_input = user_input
                self._children = client.get_children()
                self._structures = client.get_structures()

                if len(self._children) == 0:
                    # No children (maybe a student account), create entry directly
                    return self.async_create_entry(
                        title=user_input[CONF_USERNAME],
                        data=user_input,
                    )

                if len(self._children) == 1:
                    # Single child, auto-select
                    child_id, child_name = next(iter(self._children.items()))
                    return self.async_create_entry(
                        title=child_name,
                        data={
                            **user_input,
                            CONF_CHILD_ID: child_id,
                            CONF_CHILD_NAME: child_name,
                            CONF_STRUCTURE_ID: self._structures[0]
                            if self._structures
                            else "",
                        },
                    )

                # Multiple children, ask which one
                return await self.async_step_child()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BASE_URL, default=DEFAULT_BASE_URL
                    ): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_child(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle child selection step."""
        if user_input is not None:
            child_id = user_input[CONF_CHILD_ID]
            child_name = self._children[child_id]

            await self.async_set_unique_id(child_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=child_name,
                data={
                    **self._user_input,
                    CONF_CHILD_ID: child_id,
                    CONF_CHILD_NAME: child_name,
                    CONF_STRUCTURE_ID: self._structures[0]
                    if self._structures
                    else "",
                },
            )

        return self.async_show_form(
            step_id="child",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CHILD_ID): vol.In(self._children),
                }
            ),
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Handle reauth when credentials expire."""
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return OnePocketOptionsFlow(config_entry)


class OnePocketOptionsFlow(OptionsFlow):
    """Handle options for ONE Pocket."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval",
                        default=self.config_entry.options.get(
                            "scan_interval", DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=60)),
                }
            ),
        )
