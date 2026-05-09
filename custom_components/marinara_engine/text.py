"""Text platform for Marinara Engine — user activity / status message."""

from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MarinaraCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MarinaraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MarinaraUserActivityText(coordinator, entry)])


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


class MarinaraUserActivityText(_MarinaraEntity, TextEntity):
    """Editable text entity for the Marinara user activity / status message."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:pencil-outline"
    _attr_native_max = 120
    _attr_name = "User activity"
    _attr_translation_key = "user_activity"

    def __init__(self, coordinator: MarinaraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_user_activity"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("userActivity", "")

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.set_user_activity(value)
