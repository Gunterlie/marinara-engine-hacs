"""DataUpdateCoordinator for Marinara Engine."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class MarinaraCoordinator(DataUpdateCoordinator[dict]):
    """Polls Marinara Engine for chats and agents."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        self.base_url = f"http://{host}:{port}"
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(
                    f"{self.base_url}/api/chats", timeout=timeout
                ) as resp:
                    resp.raise_for_status()
                    chats = await resp.json()

                async with session.get(
                    f"{self.base_url}/api/agents", timeout=timeout
                ) as resp:
                    resp.raise_for_status()
                    agents = await resp.json()

            return {"chats": chats, "agents": agents}
        except aiohttp.ClientConnectionError as err:
            raise UpdateFailed(f"Cannot reach Marinara Engine: {err}") from err
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(f"Marinara Engine returned error {err.status}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_verify_connection(self) -> None:
        """Raise ConfigEntryNotReady if the server is unreachable."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/chats",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    resp.raise_for_status()
        except Exception as err:
            raise ConfigEntryNotReady(
                f"Cannot connect to Marinara Engine at {self.base_url}: {err}"
            ) from err

    async def send_message(self, chat_id: str, content: str, role: str = "user") -> None:
        """POST a message to a chat."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chats/{chat_id}/messages",
                json={"chatId": chat_id, "role": role, "content": content, "characterId": None},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()

    async def trigger_generation(
        self, chat_id: str, user_message: str | None = None
    ) -> None:
        """Start AI generation for a chat (fire-and-forget, non-streaming)."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "chatId": chat_id,
                    "userMessage": user_message,
                    "streaming": False,
                    "userStatus": "active",
                },
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                resp.raise_for_status()

    async def abort_generation(self) -> None:
        """Cancel any in-flight generation."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate/abort",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                resp.raise_for_status()

    async def set_agent_enabled(self, agent_id: str, enabled: bool) -> None:
        """Toggle global enabled state for an agent."""
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}/api/agents/{agent_id}",
                json={"enabled": str(enabled).lower()},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()

    async def sync_tools(self, webhook_url: str) -> tuple[int, int]:
        """Create or update all HA tool definitions in Marinara.

        Returns (created, skipped) counts.
        """
        from .const import TOOL_DEFINITIONS

        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=10)

            # Fetch existing tools so we can skip duplicates
            async with session.get(
                f"{self.base_url}/api/custom-tools", timeout=timeout
            ) as resp:
                resp.raise_for_status()
                existing = await resp.json()

            existing_names = {t["name"] for t in existing}

            created = 0
            skipped = 0
            for tool in TOOL_DEFINITIONS:
                if tool["name"] in existing_names:
                    skipped += 1
                    continue
                payload = {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parametersSchema": tool["parametersSchema"],
                    "executionType": "webhook",
                    "webhookUrl": webhook_url,
                    "enabled": True,
                }
                async with session.post(
                    f"{self.base_url}/api/custom-tools",
                    json=payload,
                    timeout=timeout,
                ) as resp:
                    resp.raise_for_status()
                created += 1

        return created, skipped
