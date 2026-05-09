"""Select platform for Marinara Engine — pick the active/primary chat."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_PRIMARY_CHAT_ID, DOMAIN
from .coordinator import MarinaraCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MarinaraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MarinaraActiveChatSelect(coordinator, entry)])


class _MarinaraEntity(CoordinatorEntity[MarinaraCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: MarinaraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

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


class MarinaraActiveChatSelect(_MarinaraEntity, SelectEntity):
    """Select which chat the services target."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:chat-processing-outline"
    _attr_name = "Active chat"
    _attr_translation_key = "active_chat"

    def __init__(self, coordinator: MarinaraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_active_chat"

    @property
    def options(self) -> list[str]:
        return [c["name"] for c in self.coordinator.data.get("chats", [])]

    @property
    def current_option(self) -> str | None:
        primary_id = self._entry.options.get(CONF_PRIMARY_CHAT_ID)
        if not primary_id:
            return None
        for chat in self.coordinator.data.get("chats", []):
            if chat["id"] == primary_id:
                return chat["name"]
        return None

    @property
    def extra_state_attributes(self) -> dict:
        primary_id = self._entry.options.get(CONF_PRIMARY_CHAT_ID)
        for chat in self.coordinator.data.get("chats", []):
            if chat["id"] == primary_id:
                return {"chat_id": primary_id, "mode": chat.get("mode")}
        return {}

    async def async_select_option(self, option: str) -> None:
        for chat in self.coordinator.data.get("chats", []):
            if chat["name"] == option:
                self.hass.config_entries.async_update_entry(
                    self._entry,
                    options={**self._entry.options, CONF_PRIMARY_CHAT_ID: chat["id"]},
                )
                return

