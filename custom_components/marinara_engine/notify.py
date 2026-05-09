"""Notify platform for Marinara Engine."""

from __future__ import annotations

import logging

from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_PRIMARY_CHAT_ID, DOMAIN
from .coordinator import MarinaraCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MarinaraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MarinaraNotifyEntity(coordinator, entry)])


class MarinaraNotifyEntity(NotifyEntity):
    """Notify entity to send messages to Marinara Engine chats."""

    _attr_has_entity_name = True
    _attr_name = "Send message"
    _attr_translation_key = "send_message"

    def __init__(self, coordinator: MarinaraCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_notify"

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Marinara Engine",
            "manufacturer": "Marinara Engine",
            "model": "Local AI Engine",
            "configuration_url": self.coordinator.base_url,
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    def _resolve_chat_id(self, target: str | None) -> str | None:
        """Resolve a target (chat name or id) to a chat_id."""
        if not target:
            return self._entry.options.get(CONF_PRIMARY_CHAT_ID)

        # Try direct ID match first
        for chat in self.coordinator.data.get("chats", []):
            if chat["id"] == target:
                return chat["id"]

        # Fall back to name match
        for chat in self.coordinator.data.get("chats", []):
            if chat.get("name") == target:
                return chat["id"]

        _LOGGER.warning(
            "Could not find chat matching target '%s'; using primary chat", target
        )
        return self._entry.options.get(CONF_PRIMARY_CHAT_ID)

    async def async_send_message(self, message: str, **kwargs) -> None:
        """Send a message to a Marinara chat.

        Supports role parameter: user, assistant, system, narrator.
        Defaults to user. Falls back to user if invalid role provided.
        """
        target = kwargs.get("target")
        chat_id = self._resolve_chat_id(target)

        if not chat_id:
            _LOGGER.error(
                "marinara_engine.notify: no target provided and no primary chat set"
            )
            return

        role = kwargs.get("role", "user")
        valid_roles = {"user", "assistant", "system", "narrator"}
        if role not in valid_roles:
            _LOGGER.warning(
                "marinara_engine.notify: invalid role '%s', falling back to 'user'. "
                "Valid roles: %s",
                role,
                ", ".join(valid_roles),
            )
            role = "user"

        await self.coordinator.send_message(chat_id, message, role=role)

        # Optionally trigger generation if requested
        if kwargs.get("trigger_generation"):
            await self.coordinator.trigger_generation(chat_id)
