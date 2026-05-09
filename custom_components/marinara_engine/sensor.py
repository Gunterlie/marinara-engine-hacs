"""Sensor platform for Marinara Engine."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    async_add_entities(
        [
            MarinaraChatCountSensor(coordinator, entry),
            MarinaraActiveAgentCountSensor(coordinator, entry),
            MarinaraVersionSensor(coordinator, entry),
            MarinaraLastSyncSensor(coordinator, entry),
        ]
    )


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


class MarinaraChatCountSensor(_MarinaraEntity, SensorEntity):
    """Total number of chats in Marinara Engine."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:chat-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "chats"
    _attr_translation_key = "chat_count"

    def __init__(self, coordinator: MarinaraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_chat_count"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("chats", []))

    @property
    def extra_state_attributes(self) -> dict:
        chats = self.coordinator.data.get("chats", [])
        by_mode: dict[str, int] = {}
        for c in chats:
            mode = c.get("mode", "unknown")
            by_mode[mode] = by_mode.get(mode, 0) + 1
        return {"by_mode": by_mode}


class MarinaraActiveAgentCountSensor(_MarinaraEntity, SensorEntity):
    """Number of globally enabled agents."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:robot-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "agents"
    _attr_translation_key = "active_agent_count"

    def __init__(self, coordinator: MarinaraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_active_agent_count"

    @property
    def native_value(self) -> int:
        agents = self.coordinator.data.get("agents", [])
        return sum(1 for a in agents if a.get("enabled") == "true")

    @property
    def extra_state_attributes(self) -> dict:
        agents = self.coordinator.data.get("agents", [])
        return {
            "total_agents": len(agents),
            "enabled_agents": [
                a.get("name") for a in agents if a.get("enabled") == "true"
            ],
        }


class MarinaraVersionSensor(_MarinaraEntity, SensorEntity):
    """Marinara Engine version."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:information-outline"
    _attr_translation_key = "version"

    def __init__(self, coordinator: MarinaraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_version"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("version")


class MarinaraLastSyncSensor(_MarinaraEntity, SensorEntity):
    """Timestamp of the last successful tool sync."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = "timestamp"
    _attr_icon = "mdi:clock-check-outline"
    _attr_translation_key = "last_sync"

    def __init__(self, coordinator: MarinaraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_last_sync"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("last_sync")
