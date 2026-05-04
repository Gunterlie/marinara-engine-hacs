"""Constants for the Marinara Engine integration."""

DOMAIN = "marinara_engine"

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 3000
SCAN_INTERVAL = 30  # seconds

CONF_HOST = "host"
CONF_PORT = "port"
CONF_WEBHOOK_ID = "webhook_id"
CONF_PRIMARY_CHAT_ID = "primary_chat_id"

# Tool definitions sent to the tool manifest endpoint.
# Each entry matches Marinara Engine's custom tool schema:
#   name, description, parametersSchema (JSON Schema object).
TOOL_DEFINITIONS = [
    {
        "name": "ha_turn_on",
        "description": "Turn on a Home Assistant entity (light, switch, fan, media player, etc.)",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID to turn on, e.g. light.living_room",
                },
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_turn_off",
        "description": "Turn off a Home Assistant entity",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID to turn off",
                },
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_toggle",
        "description": "Toggle a Home Assistant entity on or off",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID to toggle",
                },
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_get_state",
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
        "name": "ha_list_entities",
        "description": "List Home Assistant entities, optionally filtered by domain",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Optional domain filter, e.g. light, switch, climate, sensor",
                },
            },
        },
    },
    {
        "name": "ha_call_service",
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
        "name": "ha_set_brightness",
        "description": "Set the brightness of a light",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Light entity ID",
                },
                "brightness_pct": {
                    "type": "number",
                    "description": "Brightness as a percentage from 0 to 100",
                },
            },
            "required": ["entity_id", "brightness_pct"],
        },
    },
    {
        "name": "ha_set_color",
        "description": "Set the RGB color of a light",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Light entity ID",
                },
                "r": {"type": "number", "description": "Red component 0-255"},
                "g": {"type": "number", "description": "Green component 0-255"},
                "b": {"type": "number", "description": "Blue component 0-255"},
            },
            "required": ["entity_id", "r", "g", "b"],
        },
    },
    {
        "name": "ha_set_color_temp",
        "description": "Set the color temperature of a light in Kelvin (warm ~2700K, cool ~6500K)",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Light entity ID",
                },
                "kelvin": {
                    "type": "number",
                    "description": "Color temperature in Kelvin, e.g. 2700 for warm white",
                },
            },
            "required": ["entity_id", "kelvin"],
        },
    },
    {
        "name": "ha_set_temperature",
        "description": "Set the target temperature on a climate device (thermostat, AC, etc.)",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Climate entity ID",
                },
                "temperature": {
                    "type": "number",
                    "description": "Target temperature in the unit configured in Home Assistant",
                },
            },
            "required": ["entity_id", "temperature"],
        },
    },
    {
        "name": "ha_set_hvac_mode",
        "description": "Set the HVAC mode of a climate device",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Climate entity ID",
                },
                "hvac_mode": {
                    "type": "string",
                    "description": "HVAC mode: off, heat, cool, heat_cool, auto, dry, fan_only",
                },
            },
            "required": ["entity_id", "hvac_mode"],
        },
    },
    {
        "name": "ha_activate_scene",
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
    {
        "name": "ha_media_play",
        "description": "Play media on a media player",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Media player entity ID",
                },
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
        "description": "Pause a media player",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Media player entity ID",
                },
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_set_volume",
        "description": "Set the volume of a media player",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Media player entity ID",
                },
                "volume_level": {
                    "type": "number",
                    "description": "Volume level from 0.0 to 1.0",
                },
            },
            "required": ["entity_id", "volume_level"],
        },
    },
    {
        "name": "ha_lock",
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
        "description": "Unlock a lock entity",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Lock entity ID",
                },
                "code": {
                    "type": "string",
                    "description": "Optional unlock code",
                },
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_open_cover",
        "description": "Open a cover (blinds, garage door, curtains, etc.)",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Cover entity ID, e.g. cover.living_room_blinds",
                },
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_close_cover",
        "description": "Close a cover (blinds, garage door, curtains, etc.)",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Cover entity ID",
                },
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "ha_set_cover_position",
        "description": "Set the position of a cover",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Cover entity ID",
                },
                "position": {
                    "type": "number",
                    "description": "Position from 0 (closed) to 100 (open)",
                },
            },
            "required": ["entity_id", "position"],
        },
    },
    {
        "name": "ha_notify",
        "description": "Send a notification via Home Assistant",
        "parametersSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Notification message",
                },
                "title": {
                    "type": "string",
                    "description": "Notification title (optional)",
                },
                "target": {
                    "type": "string",
                    "description": "Notification service target, e.g. notify.mobile_app_phone (optional, defaults to notify.notify)",
                },
            },
            "required": ["message"],
        },
    },
]
