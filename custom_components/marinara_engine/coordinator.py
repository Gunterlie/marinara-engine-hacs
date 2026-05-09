"""DataUpdateCoordinator for Marinara Engine."""

from __future__ import annotations

import json
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

    def __init__(
        self,
        hass: HomeAssistant,
        base_url: str,
        basic_auth_user: str | None = None,
        basic_auth_pass: str | None = None,
        admin_secret: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._basic_auth = None
        user = (basic_auth_user or "").strip() or None
        password = (basic_auth_pass or "").strip() or None
        if user and password:
            self._basic_auth = aiohttp.BasicAuth(user, password)
        self._admin_secret = (admin_secret or "").strip() or None
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

                # Health check also fetches version (no auth required)
                version = None
                try:
                    async with session.get(
                        f"{self.base_url}/api/health", timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        if resp.status == 200:
                            health = await resp.json()
                            version = health.get("version")
                except Exception:
                    pass

                async with session.get(
                    f"{self.base_url}/api/chats", auth=self._basic_auth, timeout=timeout
                ) as resp:
                    resp.raise_for_status()
                    chats = await resp.json()

                async with session.get(
                    f"{self.base_url}/api/agents", auth=self._basic_auth, timeout=timeout
                ) as resp:
                    resp.raise_for_status()
                    agents = await resp.json()

                async with session.get(
                    f"{self.base_url}/api/app-settings/ui", auth=self._basic_auth, timeout=timeout
                ) as resp:
                    resp.raise_for_status()
                    ui_settings_raw = await resp.json()

            user_activity = ""
            try:
                blob = json.loads(ui_settings_raw.get("value") or "{}")
                user_activity = blob.get("userActivity", "")
            except Exception:
                pass

            return {
                "chats": chats,
                "agents": agents,
                "userActivity": user_activity,
                "version": version,
                "last_sync": self.data.get("last_sync") if self.data else None,
            }
        except aiohttp.ClientConnectionError as err:
            raise UpdateFailed(f"Cannot reach Marinara Engine: {err}") from err
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(f"Marinara Engine returned error {err.status}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    @property
    def _privileged_headers(self) -> dict:
        if self._admin_secret:
            _LOGGER.debug(
                "Sending X-Admin-Secret header (length=%d, first_char=%r)",
                len(self._admin_secret),
                self._admin_secret[0],
            )
            return {"X-Admin-Secret": self._admin_secret}
        _LOGGER.warning(
            "No admin_secret configured — privileged API calls will fail; "
            "set Admin Secret in Settings → Devices & Services → Marinara Engine → Configure"
        )
        return {}

    async def async_verify_connection(self) -> None:
        """Raise ConfigEntryNotReady if the server is unreachable."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/chats",
                    auth=self._basic_auth,
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
                auth=self._basic_auth,
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
                auth=self._basic_auth,
                json={
                    "chatId": chat_id,
                    "userMessage": user_message,
                    "streaming": False,
                },
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                resp.raise_for_status()

    async def abort_generation(self) -> None:
        """Cancel any in-flight generation."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate/abort",
                auth=self._basic_auth,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                resp.raise_for_status()

    async def _update_ui_settings(self, patch: dict) -> None:
        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(
                f"{self.base_url}/api/app-settings/ui", auth=self._basic_auth, timeout=timeout
            ) as resp:
                resp.raise_for_status()
                raw = await resp.json()
            try:
                blob = json.loads(raw.get("value") or "{}")
            except Exception:
                blob = {}
            blob.update(patch)
            async with session.put(
                f"{self.base_url}/api/app-settings/ui",
                auth=self._basic_auth,
                json={"value": json.dumps(blob)},
                timeout=timeout,
            ) as resp:
                resp.raise_for_status()
        await self.async_refresh()

    async def set_user_activity(self, activity: str) -> None:
        await self._update_ui_settings({"userActivity": activity[:120]})

    async def set_agent_enabled(self, agent_id: str, enabled: bool) -> None:
        """Toggle global enabled state for an agent."""
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}/api/agents/{agent_id}",
                auth=self._basic_auth,
                json={"enabled": enabled},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()

    async def sync_agent(self, enabled_categories: list[str]) -> str:
        """Create or update the Home Assistant agent in Marinara.

        Returns "created", "updated", or "unchanged".
        """
        from .const import build_agent_prompt, tools_for_categories

        tool_names = [t["name"] for t in tools_for_categories(enabled_categories)]
        prompt = build_agent_prompt(self.hass)

        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=10)

            async with session.get(
                f"{self.base_url}/api/agents", auth=self._basic_auth, timeout=timeout
            ) as resp:
                resp.raise_for_status()
                agents = await resp.json()

            existing = next(
                (a for a in agents if a.get("type") == "home_assistant"), None
            )

            if existing is not None:
                settings = existing.get("settings") or {}
                if isinstance(settings, str):
                    settings = json.loads(settings)
                current_tools = settings.get("enabledTools", [])
                current_prompt = existing.get("promptTemplate", "")
                tools_match = set(current_tools) == set(tool_names)
                prompt_match = current_prompt == prompt
                if tools_match and prompt_match:
                    return "unchanged"
                async with session.patch(
                    f"{self.base_url}/api/agents/{existing['id']}",
                    auth=self._basic_auth,
                    json={
                        "settings": {"enabledTools": tool_names},
                        "promptTemplate": prompt,
                    },
                    headers=self._privileged_headers,
                    timeout=timeout,
                ) as resp:
                    resp.raise_for_status()
                return "updated"

            payload = {
                "type": "home_assistant",
                "name": "Home Assistant",
                "description": (
                    "Controls Home Assistant smart home devices — lights, climate, "
                    "covers, locks, media players, scenes, and scripts."
                ),
                "phase": "parallel",
                "enabled": True,
                "connectionId": None,
                "promptTemplate": prompt,
                "settings": {"enabledTools": tool_names},
            }
            async with session.post(
                f"{self.base_url}/api/agents",
                auth=self._basic_auth,
                json=payload,
                headers=self._privileged_headers,
                timeout=timeout,
            ) as resp:
                resp.raise_for_status()

        return "created"

    async def sync_tools(
        self, webhook_url: str, enabled_categories: list[str]
    ) -> tuple[int, int]:
        """Upsert HA tool definitions into Marinara for the given categories.

        Creates missing tools and updates existing ones so schema changes propagate.
        Returns (created, updated) counts.
        """
        from .const import tools_for_categories

        tools = tools_for_categories(enabled_categories)

        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=10)

            async with session.get(
                f"{self.base_url}/api/custom-tools", auth=self._basic_auth, timeout=timeout
            ) as resp:
                resp.raise_for_status()
                existing = await resp.json()

            existing_by_name = {t["name"]: t for t in existing}

            created = 0
            updated = 0
            for tool in tools:
                payload = {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parametersSchema": tool["parametersSchema"],
                    "executionType": "webhook",
                    "webhookUrl": webhook_url,
                    "enabled": True,
                }
                if tool["name"] in existing_by_name:
                    tool_id = existing_by_name[tool["name"]]["id"]
                    async with session.patch(
                        f"{self.base_url}/api/custom-tools/{tool_id}",
                        auth=self._basic_auth,
                        json=payload,
                        headers=self._privileged_headers,
                        timeout=timeout,
                    ) as resp:
                        resp.raise_for_status()
                    updated += 1
                else:
                    async with session.post(
                        f"{self.base_url}/api/custom-tools",
                        auth=self._basic_auth,
                        json=payload,
                        headers=self._privileged_headers,
                        timeout=timeout,
                    ) as resp:
                        resp.raise_for_status()
                    created += 1

        return created, updated
