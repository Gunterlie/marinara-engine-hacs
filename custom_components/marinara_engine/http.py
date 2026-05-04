"""HTTP view that serves tool definitions pre-filled with the webhook URL.

Visit GET /api/marinara_engine/tools/<webhook_id> to download a JSON array
of custom tool objects ready to paste into Marinara Engine's Custom Tools UI.
"""

from __future__ import annotations

import json

from aiohttp import web

from homeassistant.components.http import HomeAssistantView

from .const import TOOL_DEFINITIONS


class MarinaraToolManifestView(HomeAssistantView):
    """Serve tool definitions pre-filled with the webhook URL."""

    url = "/api/marinara_engine/tools/{webhook_id}"
    name = "api:marinara_engine:tools"
    requires_auth = False  # Marinara needs to fetch this without a token

    def __init__(self, webhook_id: str) -> None:
        self._webhook_id = webhook_id

    async def get(self, request: web.Request, webhook_id: str) -> web.Response:
        if webhook_id != self._webhook_id:
            return web.Response(status=404, text="Not found")

        base_url = str(request.url.origin())
        webhook_url = f"{base_url}/api/webhook/{webhook_id}"

        tools = [
            {
                "name": t["name"],
                "description": t["description"],
                "parametersSchema": t["parametersSchema"],
                "executionType": "webhook",
                "webhookUrl": webhook_url,
                "enabled": True,
            }
            for t in TOOL_DEFINITIONS
        ]

        return web.Response(
            body=json.dumps(tools, indent=2),
            content_type="application/json",
        )
