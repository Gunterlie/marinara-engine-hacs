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
    BooleanSelector,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_ADMIN_SECRET,
    CONF_BASIC_AUTH_PASS,
    CONF_BASIC_AUTH_USER,
    CONF_ENABLED_CATEGORIES,
    CONF_INCLUDE_DEVICE_LIST,
    CONF_PRIMARY_CHAT_ID,
    CONF_URL,
    CONF_WEBHOOK_ID,
    DEFAULT_ENABLED_CATEGORIES,
    DEFAULT_URL,
    DOMAIN,
    TOOL_CATEGORIES,
)

_LOGGER = logging.getLogger(__name__)

_STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_URL, default=DEFAULT_URL
        ): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)
        ),
        vol.Optional(CONF_BASIC_AUTH_USER, default=""): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Optional(CONF_BASIC_AUTH_PASS, default=""): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Optional(CONF_ADMIN_SECRET, default=""): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
    }
)


async def _test_connection(
    url: str,
    basic_auth_user: str | None = None,
    basic_auth_pass: str | None = None,
) -> str | None:
    """Return None on success or an error key string on failure."""
    auth = None
    user = (basic_auth_user or "").strip() or None
    password = (basic_auth_pass or "").strip() or None
    if user and password:
        auth = aiohttp.BasicAuth(user, password)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{url.rstrip('/')}/api/chats",
                auth=auth,
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

    VERSION = 2

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            basic_auth_user = user_input.get(CONF_BASIC_AUTH_USER, "").strip() or None
            basic_auth_pass = user_input.get(CONF_BASIC_AUTH_PASS, "").strip() or None
            admin_secret = user_input.get(CONF_ADMIN_SECRET, "").strip() or None

            error = await _test_connection(url, basic_auth_user, basic_auth_pass)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Marinara Engine ({url})",
                    data={
                        CONF_URL: url,
                        CONF_WEBHOOK_ID: async_generate_id(),
                        CONF_BASIC_AUTH_USER: basic_auth_user,
                        CONF_BASIC_AUTH_PASS: basic_auth_pass,
                        CONF_ADMIN_SECRET: admin_secret,
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
            # Strip secrets; treat empty string as None
            for key in (CONF_ADMIN_SECRET, CONF_BASIC_AUTH_USER, CONF_BASIC_AUTH_PASS):
                if key in data and isinstance(data[key], str):
                    data[key] = data[key].strip() or None

            # Update connection credentials in entry.data so coordinator picks them up
            new_data = dict(self._config_entry.data)
            new_data[CONF_BASIC_AUTH_USER] = data.pop(CONF_BASIC_AUTH_USER, None)
            new_data[CONF_BASIC_AUTH_PASS] = data.pop(CONF_BASIC_AUTH_PASS, None)
            new_data[CONF_ADMIN_SECRET] = data.pop(CONF_ADMIN_SECRET, None)
            self.hass.config_entries.async_update_entry(
                self._config_entry, data=new_data
            )

            return self.async_create_entry(title="", data=data)

        url = self._config_entry.data[CONF_URL]
        basic_auth_user = self._config_entry.data.get(CONF_BASIC_AUTH_USER)
        basic_auth_pass = self._config_entry.data.get(CONF_BASIC_AUTH_PASS)
        auth = None
        if basic_auth_user and basic_auth_pass:
            auth = aiohttp.BasicAuth(basic_auth_user, basic_auth_pass)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{url}/api/chats",
                    auth=auth,
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
        current_admin_secret = self._config_entry.data.get(CONF_ADMIN_SECRET, "")
        current_basic_auth_user = self._config_entry.data.get(CONF_BASIC_AUTH_USER, "")
        current_basic_auth_pass = self._config_entry.data.get(CONF_BASIC_AUTH_PASS, "")
        current_include_device_list = self._config_entry.options.get(CONF_INCLUDE_DEVICE_LIST, False)

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
                vol.Optional(
                    CONF_BASIC_AUTH_USER, default=current_basic_auth_user or ""
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Optional(
                    CONF_BASIC_AUTH_PASS, default=current_basic_auth_pass or ""
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                vol.Optional(
                    CONF_ADMIN_SECRET, default=current_admin_secret or ""
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                vol.Optional(
                    CONF_INCLUDE_DEVICE_LIST, default=current_include_device_list
                ): BooleanSelector(),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
