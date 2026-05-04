"""Webhook handler: receives tool calls from Marinara Engine and executes HA actions."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from homeassistant.components.webhook import (
    async_register,
    async_unregister,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def async_register_webhook(hass: HomeAssistant, webhook_id: str) -> None:
    async_register(
        hass,
        DOMAIN,
        "Marinara Engine",
        webhook_id,
        _handle_webhook,
        allowed_methods=["POST"],
    )


def async_unregister_webhook(hass: HomeAssistant, webhook_id: str) -> None:
    async_unregister(hass, webhook_id)


async def _handle_webhook(
    hass: HomeAssistant, webhook_id: str, request: web.Request
) -> web.Response:
    """Dispatch an incoming tool call to the appropriate HA action."""
    try:
        body = await request.json()
    except Exception:
        return web.Response(status=400, text="Invalid JSON body")

    tool: str = body.get("tool", "")
    args: dict[str, Any] = body.get("arguments", {})

    _LOGGER.debug("Marinara webhook: tool=%s args=%s", tool, args)

    handler = _DISPATCH.get(tool)
    if handler is None:
        _LOGGER.warning("Marinara webhook: unknown tool '%s'", tool)
        return web.json_response({"error": f"Unknown tool: {tool}"}, status=400)

    try:
        result = await handler(hass, args)
    except Exception as err:
        _LOGGER.error("Marinara webhook: tool '%s' failed: %s", tool, err)
        return web.json_response({"error": str(err)}, status=500)

    return web.json_response(result)


async def _turn_on(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    await hass.services.async_call(
        "homeassistant", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    return {"result": f"Turned on {entity_id}"}


async def _turn_off(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    await hass.services.async_call(
        "homeassistant", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    return {"result": f"Turned off {entity_id}"}


async def _toggle(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    await hass.services.async_call(
        "homeassistant", "toggle", {"entity_id": entity_id}, blocking=True
    )
    return {"result": f"Toggled {entity_id}"}


async def _get_state(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    state = hass.states.get(entity_id)
    if state is None:
        return {"error": f"Entity '{entity_id}' not found"}
    return {
        "entity_id": entity_id,
        "state": state.state,
        "attributes": dict(state.attributes),
        "last_updated": state.last_updated.isoformat(),
    }


async def _list_entities(hass: HomeAssistant, args: dict) -> dict:
    domain_filter: str | None = args.get("domain")
    states = hass.states.async_all(domain_filter)
    return {
        "entities": [
            {
                "entity_id": s.entity_id,
                "state": s.state,
                "friendly_name": s.attributes.get("friendly_name"),
            }
            for s in states
        ]
    }


async def _call_service(hass: HomeAssistant, args: dict) -> dict:
    domain = _require(args, "domain")
    service = _require(args, "service")
    data: dict = dict(args.get("data") or {})
    entity_id = args.get("entity_id")
    if entity_id:
        data["entity_id"] = entity_id
    await hass.services.async_call(domain, service, data, blocking=True)
    return {"result": f"Called {domain}.{service}"}


async def _set_brightness(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    brightness_pct = _require(args, "brightness_pct")
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, "brightness_pct": float(brightness_pct)},
        blocking=True,
    )
    return {"result": f"Set {entity_id} brightness to {brightness_pct}%"}


async def _set_color(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    r = int(_require(args, "r"))
    g = int(_require(args, "g"))
    b = int(_require(args, "b"))
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, "rgb_color": [r, g, b]},
        blocking=True,
    )
    return {"result": f"Set {entity_id} color to rgb({r},{g},{b})"}


async def _set_color_temp(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    kelvin = int(_require(args, "kelvin"))
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, "kelvin": kelvin},
        blocking=True,
    )
    return {"result": f"Set {entity_id} color temperature to {kelvin}K"}


async def _set_temperature(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    temperature = float(_require(args, "temperature"))
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": entity_id, "temperature": temperature},
        blocking=True,
    )
    return {"result": f"Set {entity_id} temperature to {temperature}"}


async def _set_hvac_mode(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    hvac_mode = _require(args, "hvac_mode")
    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": entity_id, "hvac_mode": hvac_mode},
        blocking=True,
    )
    return {"result": f"Set {entity_id} HVAC mode to {hvac_mode}"}


async def _activate_scene(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    await hass.services.async_call(
        "scene", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    return {"result": f"Activated scene {entity_id}"}


async def _run_script(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    await hass.services.async_call(
        "script", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    return {"result": f"Ran script {entity_id}"}


async def _media_play(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    data: dict = {"entity_id": entity_id}
    if args.get("media_content_id"):
        data["media_content_id"] = args["media_content_id"]
        data["media_content_type"] = args.get("media_content_type", "music")
        await hass.services.async_call(
            "media_player", "play_media", data, blocking=True
        )
    else:
        await hass.services.async_call(
            "media_player", "media_play", {"entity_id": entity_id}, blocking=True
        )
    return {"result": f"Playing on {entity_id}"}


async def _media_pause(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    await hass.services.async_call(
        "media_player", "media_pause", {"entity_id": entity_id}, blocking=True
    )
    return {"result": f"Paused {entity_id}"}


async def _set_volume(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    volume_level = float(_require(args, "volume_level"))
    await hass.services.async_call(
        "media_player",
        "volume_set",
        {"entity_id": entity_id, "volume_level": volume_level},
        blocking=True,
    )
    return {"result": f"Set {entity_id} volume to {volume_level}"}


async def _lock(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    await hass.services.async_call(
        "lock", "lock", {"entity_id": entity_id}, blocking=True
    )
    return {"result": f"Locked {entity_id}"}


async def _unlock(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    data: dict = {"entity_id": entity_id}
    if args.get("code"):
        data["code"] = args["code"]
    await hass.services.async_call("lock", "unlock", data, blocking=True)
    return {"result": f"Unlocked {entity_id}"}


async def _open_cover(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    await hass.services.async_call(
        "cover", "open_cover", {"entity_id": entity_id}, blocking=True
    )
    return {"result": f"Opened {entity_id}"}


async def _close_cover(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    await hass.services.async_call(
        "cover", "close_cover", {"entity_id": entity_id}, blocking=True
    )
    return {"result": f"Closed {entity_id}"}


async def _set_cover_position(hass: HomeAssistant, args: dict) -> dict:
    entity_id = _require(args, "entity_id")
    position = int(_require(args, "position"))
    await hass.services.async_call(
        "cover",
        "set_cover_position",
        {"entity_id": entity_id, "position": position},
        blocking=True,
    )
    return {"result": f"Set {entity_id} position to {position}%"}


async def _notify(hass: HomeAssistant, args: dict) -> dict:
    message = _require(args, "message")
    target = args.get("target", "notify.notify")
    parts = target.split(".", 1)
    domain = parts[0] if len(parts) == 2 else "notify"
    service = parts[1] if len(parts) == 2 else "notify"
    data: dict = {"message": message}
    if args.get("title"):
        data["title"] = args["title"]
    await hass.services.async_call(domain, service, data, blocking=True)
    return {"result": "Notification sent"}


_DISPATCH = {
    "ha_turn_on": _turn_on,
    "ha_turn_off": _turn_off,
    "ha_toggle": _toggle,
    "ha_get_state": _get_state,
    "ha_list_entities": _list_entities,
    "ha_call_service": _call_service,
    "ha_set_brightness": _set_brightness,
    "ha_set_color": _set_color,
    "ha_set_color_temp": _set_color_temp,
    "ha_set_temperature": _set_temperature,
    "ha_set_hvac_mode": _set_hvac_mode,
    "ha_activate_scene": _activate_scene,
    "ha_run_script": _run_script,
    "ha_media_play": _media_play,
    "ha_media_pause": _media_pause,
    "ha_set_volume": _set_volume,
    "ha_lock": _lock,
    "ha_unlock": _unlock,
    "ha_open_cover": _open_cover,
    "ha_close_cover": _close_cover,
    "ha_set_cover_position": _set_cover_position,
    "ha_notify": _notify,
}


def _require(args: dict, key: str) -> Any:
    value = args.get(key)
    if value is None:
        raise ValueError(f"Missing required argument: {key}")
    return value
