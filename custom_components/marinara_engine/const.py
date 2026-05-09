"""Constants for the Marinara Engine integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

DOMAIN = "marinara_engine"

DEFAULT_URL = "http://localhost:7860"
SCAN_INTERVAL = 30  # seconds

CONF_URL = "url"
CONF_WEBHOOK_ID = "webhook_id"
CONF_PRIMARY_CHAT_ID = "primary_chat_id"
CONF_ENABLED_CATEGORIES = "enabled_categories"
CONF_BASIC_AUTH_USER = "basic_auth_user"
CONF_BASIC_AUTH_PASS = "basic_auth_pass"
CONF_ADMIN_SECRET = "admin_secret"

# Legacy constants kept for v1 → v2 migration
CONF_HOST = "host"
CONF_PORT = "port"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 7860

CONTROLLABLE_DOMAINS: frozenset[str] = frozenset({
    "light", "switch", "climate", "cover", "media_player",
    "lock", "fan", "vacuum", "scene", "script", "alarm_control_panel",
})

TOOL_CATEGORIES: dict[str, str] = {
    "lights": "Lights & Switches",
    "climate": "Climate",
    "covers": "Covers (Blinds & Garage)",
    "locks": "Locks",
    "media": "Media Players",
    "scenes_scripts": "Scenes & Scripts",
    "query": "Query & Generic",
}

# Locks excluded by default — users can opt in via Options
DEFAULT_ENABLED_CATEGORIES: list[str] = [
    "lights",
    "climate",
    "covers",
    "media",
    "scenes_scripts",
    "query",
]

# Each tool carries a "category" key matching TOOL_CATEGORIES above.
TOOL_DEFINITIONS = [
    # ------------------------------------------------------------------ lights
    {
        "name": "ha_turn_on",
        "category": "lights",
        "description": (
            "Turn on a Home Assistant entity or all entities of a given domain in an area. "
            "Provide entity_id for a single entity, or area_name (+ optional domain, default 'light') "
            "to turn on everything in a room at once."
        ),
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID to turn on, e.g. light.living_room",
                },
                "area_name": {
                    "type": "string",
                    "description": "Area name to target, e.g. Büro. Turns on all entities of the given domain in that area.",
                },
                "domain": {
                    "type": "string",
                    "description": "Domain to target when using area_name (default: light), e.g. light, switch, fan",
                },
            },
        },
    },
    {
        "name": "ha_turn_off",
        "category": "lights",
        "description": (
            "Turn off a Home Assistant entity or all entities of a given domain in an area. "
            "Provide entity_id for a single entity, or area_name (+ optional domain, default 'light')."
        ),
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID to turn off",
                },
                "area_name": {
                    "type": "string",
                    "description": "Area name to target, e.g. Büro",
                },
                "domain": {
                    "type": "string",
                    "description": "Domain to target when using area_name (default: light)",
                },
            },
        },
    },
    {
        "name": "ha_toggle",
        "category": "lights",
        "description": (
            "Toggle a Home Assistant entity or all entities of a given domain in an area. "
            "Provide entity_id for a single entity, or area_name (+ optional domain, default 'light')."
        ),
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID to toggle",
                },
                "area_name": {
                    "type": "string",
                    "description": "Area name to target, e.g. Büro",
                },
                "domain": {
                    "type": "string",
                    "description": "Domain to target when using area_name (default: light)",
                },
            },
        },
    },
    {
        "name": "ha_set_brightness",
        "category": "lights",
        "description": "Set the brightness of a light or all lights in an area",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Light entity ID"},
                "area_name": {"type": "string", "description": "Area name to target all lights in that room"},
                "brightness_pct": {
                    "type": "number",
                    "description": "Brightness as a percentage from 0 to 100",
                },
            },
            "required": ["brightness_pct"],
        },
    },
    {
        "name": "ha_set_color",
        "category": "lights",
        "description": "Set the RGB color of a light or all lights in an area",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Light entity ID"},
                "area_name": {"type": "string", "description": "Area name to target all lights in that room"},
                "r": {"type": "number", "description": "Red component 0-255"},
                "g": {"type": "number", "description": "Green component 0-255"},
                "b": {"type": "number", "description": "Blue component 0-255"},
            },
            "required": ["r", "g", "b"],
        },
    },
    {
        "name": "ha_set_color_temp",
        "category": "lights",
        "description": "Set the color temperature of a light or all lights in an area",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Light entity ID"},
                "area_name": {"type": "string", "description": "Area name to target all lights in that room"},
                "kelvin": {
                    "type": "number",
                    "description": "Color temperature in Kelvin, e.g. 2700 for warm white, 6500 for cool daylight",
                },
            },
            "required": ["kelvin"],
        },
    },
    # ----------------------------------------------------------------- climate
    {
        "name": "ha_set_temperature",
        "category": "climate",
        "description": "Set the target temperature on a climate device or all climate devices in an area",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Climate entity ID"},
                "area_name": {"type": "string", "description": "Area name to target all climate devices in that room"},
                "temperature": {
                    "type": "number",
                    "description": "Target temperature in the unit configured in Home Assistant",
                },
            },
            "required": ["temperature"],
        },
    },
    {
        "name": "ha_set_hvac_mode",
        "category": "climate",
        "description": "Set the HVAC mode of a climate device or all climate devices in an area",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Climate entity ID"},
                "area_name": {"type": "string", "description": "Area name to target all climate devices in that room"},
                "hvac_mode": {
                    "type": "string",
                    "description": "HVAC mode: off, heat, cool, heat_cool, auto, dry, fan_only",
                },
            },
            "required": ["hvac_mode"],
        },
    },
    # ------------------------------------------------------------------ covers
    {
        "name": "ha_open_cover",
        "category": "covers",
        "description": "Open a cover or all covers in an area (blinds, garage door, curtains, etc.)",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Cover entity ID, e.g. cover.living_room_blinds",
                },
                "area_name": {"type": "string", "description": "Area name to open all covers in that room"},
            },
        },
    },
    {
        "name": "ha_close_cover",
        "category": "covers",
        "description": "Close a cover or all covers in an area (blinds, garage door, curtains, etc.)",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Cover entity ID"},
                "area_name": {"type": "string", "description": "Area name to close all covers in that room"},
            },
        },
    },
    {
        "name": "ha_set_cover_position",
        "category": "covers",
        "description": "Set the position of a cover or all covers in an area",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Cover entity ID"},
                "area_name": {"type": "string", "description": "Area name to set position for all covers in that room"},
                "position": {
                    "type": "number",
                    "description": "Position from 0 (closed) to 100 (open)",
                },
            },
            "required": ["position"],
        },
    },
    # ------------------------------------------------------------------- locks
    {
        "name": "ha_lock",
        "category": "locks",
        "description": "Lock a lock entity",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Lock entity ID, e.g. lock.front_door",
                },
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_unlock",
        "category": "locks",
        "description": "Unlock a lock entity",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Lock entity ID"},
                "code": {"type": "string", "description": "Optional unlock code"},
            },
            "required": ["entity_id"],
        },
    },
    # ------------------------------------------------------------------- media
    {
        "name": "ha_media_play",
        "category": "media",
        "description": "Play media on a media player",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Media player entity ID"},
                "media_content_id": {
                    "type": "string",
                    "description": "URL or identifier of the media to play (optional)",
                },
                "media_content_type": {
                    "type": "string",
                    "description": "Type of media: music, tvshow, movie, playlist (optional)",
                },
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_media_pause",
        "category": "media",
        "description": "Pause a media player",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Media player entity ID"},
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_set_volume",
        "category": "media",
        "description": "Set the volume of a media player",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Media player entity ID"},
                "volume_level": {
                    "type": "number",
                    "description": "Volume level from 0.0 to 1.0",
                },
            },
            "required": ["entity_id", "volume_level"],
        },
    },
    # ---------------------------------------------------------- scenes/scripts
    {
        "name": "ha_activate_scene",
        "category": "scenes_scripts",
        "description": "Activate a Home Assistant scene",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Scene entity ID, e.g. scene.movie_night",
                },
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_run_script",
        "category": "scenes_scripts",
        "description": "Run a Home Assistant script",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Script entity ID, e.g. script.welcome_home",
                },
            },
            "required": ["entity_id"],
        },
    },
    # --------------------------------------------------------------- query/generic
    {
        "name": "ha_get_state",
        "category": "query",
        "description": "Get the current state and attributes of a Home Assistant entity",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID to query, e.g. sensor.temperature",
                },
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_list_areas",
        "category": "query",
        "description": "List all areas (rooms) configured in Home Assistant with their IDs and names",
        "parametersSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "ha_list_entities",
        "category": "query",
        "description": (
            "List Home Assistant entities. Internal/diagnostic domains (update, device_tracker, "
            "person, zone, sun, weather, automation) and hidden/disabled entities are excluded by default. "
            "Use domain and/or area_name to narrow results further. "
            "Returns up to `limit` entities (default 100) plus a `total` count so you know if results were truncated."
        ),
        "parametersSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Optional domain filter, e.g. light, switch, climate, sensor",
                },
                "area_name": {
                    "type": "string",
                    "description": "Optional area name filter, e.g. Büro — returns only entities in that room",
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of entities to return (default: 100, max: 500)",
                },
            },
        },
    },
    {
        "name": "ha_call_service",
        "category": "query",
        "description": "Call any Home Assistant service with full control over domain, service, and data",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Service domain, e.g. light, switch, climate, script",
                },
                "service": {
                    "type": "string",
                    "description": "Service name, e.g. turn_on, set_temperature, press",
                },
                "entity_id": {
                    "type": "string",
                    "description": "Target entity ID (optional)",
                },
                "data": {
                    "type": "object",
                    "description": "Additional service data as key/value pairs (optional)",
                },
            },
            "required": ["domain", "service"],
        },
    },
    {
        "name": "ha_notify",
        "category": "query",
        "description": "Send a notification via Home Assistant",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Notification message"},
                "title": {"type": "string", "description": "Notification title (optional)"},
                "target": {
                    "type": "string",
                    "description": "Notification service target, e.g. notify.mobile_app_phone (optional)",
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "ha_search_entities",
        "category": "query",
        "description": (
            "Search for Home Assistant entities by name. Returns the top matches ranked "
            "by relevance with their entity_id, friendly name, area, and current state. "
            "Use this when you know a device's common name but not its exact entity_id."
        ),
        "parametersSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query — e.g. 'office light', 'bedroom ac', 'front door'",
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum results to return (default: 5, max: 20)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "ha_get_home_summary",
        "category": "query",
        "description": (
            "Get a compact snapshot of the entire home state. Returns all controllable "
            "devices grouped by area with their current state, plus presence info (who is home) "
            "and current weather. Use this to quickly understand the state of the home."
        ),
        "parametersSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


def tools_for_categories(enabled_categories: list[str]) -> list[dict]:
    """Return tool definitions whose category is in enabled_categories."""
    cats = set(enabled_categories)
    return [t for t in TOOL_DEFINITIONS if t["category"] in cats]


_AGENT_GUIDELINES = """\
Guidelines:
- Execute commands directly when the user asks. \
"Turn on the office lights" → call ha_turn_on with entity_id from the device list above.
- Use the exact entity_id from the device list. Every controllable device is listed above \
with its current state.
- If a device is not listed, call ha_search_entities to find it by name.
- Use area_name instead of individual entity_ids when you want to control all devices \
in a room at once.
- If you don't know the exact area name, call ha_list_areas first, then act.
- Prefer specific tools (ha_set_brightness, ha_set_color) over ha_call_service \
unless no dedicated tool fits.
- Do not invent entity IDs. Use the device list above or query first if unsure.
- Report errors clearly so the user can correct them.
"""


def build_agent_prompt(hass: HomeAssistant) -> str:
    """Build a dynamic agent prompt containing the live entity catalog."""
    from homeassistant.helpers import area_registry as ar_helper
    from homeassistant.helpers import entity_registry as er_helper

    ar = ar_helper.async_get(hass)
    er = er_helper.async_get(hass)

    area_names: dict[str, str] = {a.id: a.name for a in ar.areas.values()}
    entity_reg = {e.entity_id: e for e in er.entities.values()}

    area_entities: dict[str, list[str]] = {name: [] for name in area_names.values()}
    unassigned: list[str] = []

    for state in hass.states.async_all():
        domain = state.entity_id.split(".")[0]
        if domain not in CONTROLLABLE_DOMAINS:
            continue

        entry = entity_reg.get(state.entity_id)
        if entry and (entry.hidden_by or entry.disabled_by):
            continue

        friendly = state.attributes.get("friendly_name", state.entity_id)
        state_str = state.state

        if domain == "light" and "brightness" in state.attributes:
            brightness = state.attributes["brightness"]
            if brightness is not None:
                pct = round(brightness / 255 * 100)
                state_str = f"{state.state}, {pct}%"
        elif domain == "climate" and "current_temperature" in state.attributes:
            state_str = f"{state.state}, {state.attributes['current_temperature']}°"

        line = f'- {state.entity_id} ("{friendly}") — {state_str}'

        if entry and entry.area_id:
            area_name = area_names.get(entry.area_id)
            if area_name:
                area_entities[area_name].append(line)
            else:
                unassigned.append(line)
        else:
            unassigned.append(line)

    sections: list[str] = [
        "You are a Home Assistant controller.",
        "You control a smart home. Here are the available devices:\n",
    ]

    for area_name in sorted(area_entities.keys()):
        entities = area_entities[area_name]
        if entities:
            sections.append(f"## {area_name}")
            for line in entities:
                sections.append(line)
            sections.append("")

    if unassigned:
        sections.append("## Unassigned")
        for line in unassigned:
            sections.append(line)
        sections.append("")

    sections.append(_AGENT_GUIDELINES)

    return "\n".join(sections)
