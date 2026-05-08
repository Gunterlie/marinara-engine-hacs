"""Config flow for Marinara Engine."""

from __future__ import annotations

import logging

import aiohttp
import voluptuous as vol

from homeassistant.components.webhook import async_generate_id
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_ADMIN_SECRET,
    CONF_ENABLED_CATEGORIES,
    CONF_HOST,
    CONF_PORT,
    CONF_PRIMARY_CHAT_ID,
    CONF_WEBHOOK_ID,
    DEFAULT_ENABLED_CATEGORIES,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DOMAIN,
    TOOL_CATEGORIES,
)

_LOGGER = logging.getLogger(__name__)

_STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
    }
)


async def _test_connection(host: str, port: int) -> str | None:
    """Return None on success or an error key string on failure."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://{host}:{port}/api/chats",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    return None
                return "cannot_connect"
    except aiohttp.ClientConnectionError:
        return "cannot_connect"
    except Exception:
        return "unknown"


class MarinaraConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Marinara Engine."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]

            error = await _test_connection(host, port)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Marinara Engine ({host}:{port})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_WEBHOOK_ID: async_generate_id(),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_STEP_USER_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MarinaraOptionsFlow(config_entry)


class MarinaraOptionsFlow(OptionsFlow):
    """Options flow: choose which chat is the primary chat for services."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry
        self._chats: list[dict] = []

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if user_input is not None:
            data = dict(user_input)
            if CONF_ADMIN_SECRET in data and isinstance(data[CONF_ADMIN_SECRET], str):
                data[CONF_ADMIN_SECRET] = data[CONF_ADMIN_SECRET].strip()
            return self.async_create_entry(title="", data=data)

        host = self._config_entry.data[CONF_HOST]
        port = self._config_entry.data[CONF_PORT]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{host}:{port}/api/chats",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    self._chats = await resp.json() if resp.status == 200 else []
        except Exception:
            self._chats = []

        chat_options = {c["id"]: c["name"] for c in self._chats}
        current_chat = self._config_entry.options.get(CONF_PRIMARY_CHAT_ID, "")
        current_cats = self._config_entry.options.get(
            CONF_ENABLED_CATEGORIES, DEFAULT_ENABLED_CATEGORIES
        )
        current_admin_secret = self._config_entry.options.get(CONF_ADMIN_SECRET, "")

        schema = vol.Schema(
            {
                vol.Optional(CONF_PRIMARY_CHAT_ID, default=current_chat): vol.In(
                    chat_options
                )
                if chat_options
                else str,
                vol.Optional(
                    CONF_ENABLED_CATEGORIES, default=current_cats
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=k, label=v)
                            for k, v in TOOL_CATEGORIES.items()
                        ],
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional(CONF_ADMIN_SECRET, default=current_admin_secret): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
