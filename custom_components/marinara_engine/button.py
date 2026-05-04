"""Button platform for Marinara Engine."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
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
    async_add_entities([MarinaraAbortButton(coordinator, entry)])


class MarinaraAbortButton(CoordinatorEntity[MarinaraCoordinator], ButtonEntity):
    """Cancel any in-flight AI generation."""

    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, coordinator: MarinaraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_abort_generation"
        self._attr_name = "Marinara Abort Generation"

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Marinara Engine",
            "manufacturer": "Marinara Engine",
            "model": "Local AI Engine",
        }

    async def async_press(self) -> None:
        await self.coordinator.abort_generation()
