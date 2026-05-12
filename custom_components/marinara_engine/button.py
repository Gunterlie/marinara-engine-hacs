"""Button platform for Marinara Engine."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ENABLED_CATEGORIES, CONF_INCLUDE_DEVICE_LIST, CONF_WEBHOOK_ID, DEFAULT_ENABLED_CATEGORIES, DOMAIN
from .coordinator import MarinaraCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MarinaraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        MarinaraAbortButton(coordinator, entry),
        MarinaraSyncToolsButton(coordinator, entry),
    ])


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


class MarinaraAbortButton(_MarinaraEntity, ButtonEntity):
    """Cancel any in-flight AI generation."""

    _attr_icon = "mdi:stop-circle-outline"
    _attr_name = "Abort generation"
    _attr_translation_key = "abort_generation"

    def __init__(self, coordinator: MarinaraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_abort_generation"

    async def async_press(self) -> None:
        await self.coordinator.abort_generation()


class MarinaraSyncToolsButton(_MarinaraEntity, ButtonEntity):
    """Push all HA tool definitions into Marinara's Custom Tools."""

    _attr_icon = "mdi:cloud-sync-outline"
    _attr_name = "Sync HA tools"
    _attr_translation_key = "sync_tools"

    def __init__(self, coordinator: MarinaraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_sync_tools"

    async def async_press(self) -> None:
        webhook_id: str = self._entry.data[CONF_WEBHOOK_ID]
        try:
            base_url = get_url(self.hass, allow_internal=True, prefer_external=False)
        except NoURLAvailableError:
            base_url = (
                f"http://{self.hass.config.api.local_ip}"
                f":{self.hass.config.api.port}"
            )
        webhook_url = f"{base_url}/api/webhook/{webhook_id}"
        enabled_categories = self._entry.options.get(
            CONF_ENABLED_CATEGORIES, DEFAULT_ENABLED_CATEGORIES
        )
        include_device_list = self._entry.options.get(CONF_INCLUDE_DEVICE_LIST, False)
        try:
            created, updated = await self.coordinator.sync_tools(webhook_url, enabled_categories)
            _LOGGER.info(
                "Marinara tool sync: %d created, %d updated", created, updated
            )
            agent_status = await self.coordinator.sync_agent(enabled_categories, include_device_list=include_device_list)
            if agent_status != "unchanged":
                _LOGGER.info("Marinara tool sync: Home Assistant agent %s", agent_status)
            light_status = await self.coordinator.sync_light_agent(include_device_list=include_device_list)
            if light_status != "unchanged":
                _LOGGER.info("Marinara tool sync: Home Assistant Light agent %s", light_status)
            # Update last_sync timestamp in coordinator data
            from datetime import datetime, timezone
            if self.coordinator.data is not None:
                self.coordinator.data["last_sync"] = datetime.now(timezone.utc).isoformat()
                await self.coordinator.async_set_updated_data(self.coordinator.data)
        except Exception as err:
            _LOGGER.error("Marinara tool sync failed: %s", err)
            raise
