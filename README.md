# Marinara Engine — Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

Connects [Marinara Engine](https://github.com/Gunterlie/Marinara-Engine) to Home Assistant so your AI characters can control real-world devices — lights, climate, locks, covers, media players, and more — directly from chat, roleplay, and game sessions.

## How it works

Marinara Engine supports **custom webhook tools**: when the AI decides to call a tool, it sends a POST to a URL you configure. This integration registers that webhook inside Home Assistant and provides 21 ready-made tools (lights, climate, locks, covers, media players, scenes, scripts, and more). On first install, all tools are automatically pushed into Marinara's Custom Tools — no manual setup required.

```
Marinara AI  →  calls tool ha_turn_on  →  webhook POST to HA  →  light turns on
Marinara AI  ←  {"result": "Turned on light.living_room"}  ←  HA responds
```

## Requirements

- Home Assistant 2024.1 or newer
- [HACS](https://hacs.xyz) installed
- [Marinara Engine](https://github.com/Gunterlie/Marinara-Engine) running locally (default: `localhost:3000`)

## Installation

### 1. Add to HACS

1. Open HACS → three-dot menu → **Custom repositories**
2. URL: `https://github.com/Gunterlie/marinara-engine-hacs`
3. Category: **Integration**
4. Click **Add**, then search for **Marinara Engine** and install it
5. Restart Home Assistant

### 2. Add the integration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Marinara Engine**
3. Enter the host and port where Marinara Engine is running (default: `localhost` / `3000`)
4. Click **Submit** — the integration will connect and automatically sync all tools to Marinara

### 3. Done

Your AI characters can now control Home Assistant entities. Open any chat in Marinara and ask your character to turn on a light, change the temperature, or activate a scene.

## Configuration

After setup, open the integration's **Configure** menu to set a **Primary Chat** — this is the default chat that the `send_message` and `trigger_generation` HA services will target when no `chat_id` is specified.

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| Marinara Chat Count | Sensor | Total number of chats |
| Marinara Active Agent Count | Sensor | Number of globally enabled agents |
| Marinara Active Chat | Select | Choose which chat HA services target |
| Marinara Agent: *name* | Switch | Enable / disable each AI agent globally |
| Marinara Abort Generation | Button | Cancel any in-flight AI generation |
| Marinara Sync HA Tools | Button | Re-sync all tool definitions to Marinara |

## Available tools

Tools are automatically created in Marinara's **Custom Tools** on install. The AI uses them during generation — you don't need to prompt for them explicitly.

### Lights
| Tool | Description |
|------|-------------|
| `ha_turn_on` | Turn on any entity |
| `ha_turn_off` | Turn off any entity |
| `ha_toggle` | Toggle any entity |
| `ha_set_brightness` | Set brightness (0–100%) |
| `ha_set_color` | Set RGB color |
| `ha_set_color_temp` | Set color temperature in Kelvin |

### Climate
| Tool | Description |
|------|-------------|
| `ha_set_temperature` | Set thermostat target temperature |
| `ha_set_hvac_mode` | Set mode: off, heat, cool, auto, … |

### Covers (blinds, garage doors)
| Tool | Description |
|------|-------------|
| `ha_open_cover` | Open a cover |
| `ha_close_cover` | Close a cover |
| `ha_set_cover_position` | Set position 0–100% |

### Locks
| Tool | Description |
|------|-------------|
| `ha_lock` | Lock a lock entity |
| `ha_unlock` | Unlock (with optional code) |

### Media players
| Tool | Description |
|------|-------------|
| `ha_media_play` | Play (optionally a specific media URL) |
| `ha_media_pause` | Pause |
| `ha_set_volume` | Set volume (0.0–1.0) |

### Scenes & scripts
| Tool | Description |
|------|-------------|
| `ha_activate_scene` | Activate a scene |
| `ha_run_script` | Run a script |

### Query & generic
| Tool | Description |
|------|-------------|
| `ha_get_state` | Get current state and attributes of any entity |
| `ha_list_entities` | List entities, optionally filtered by domain |
| `ha_call_service` | Call any HA service with full control |
| `ha_notify` | Send a notification |

## HA Services

Use these in automations to interact with Marinara from Home Assistant's side.

### `marinara_engine.send_message`

Send a message to a Marinara chat.

| Field | Required | Description |
|-------|----------|-------------|
| `message` | Yes | Message content |
| `chat_id` | No | Target chat ID (defaults to primary chat) |
| `role` | No | `user` / `assistant` / `system` / `narrator` |
| `trigger_generation` | No | Also trigger an AI response (default: false) |

**Example automation:**
```yaml
automation:
  trigger:
    platform: state
    entity_id: binary_sensor.front_door
    to: "on"
  action:
    service: marinara_engine.send_message
    data:
      message: "Someone just arrived at the front door."
      trigger_generation: true
```

### `marinara_engine.trigger_generation`

Start an AI generation turn in a chat.

| Field | Required | Description |
|-------|----------|-------------|
| `chat_id` | No | Target chat ID (defaults to primary chat) |
| `user_message` | No | Optional user message to include |

## Re-syncing tools

If you add new tools in a future update or accidentally delete tools from Marinara, press the **Marinara Sync HA Tools** button in the integration's device page. It skips tools that already exist and only creates missing ones.

## Troubleshooting

**Tools not appearing in Marinara**
Press the **Marinara Sync HA Tools** button, or restart Home Assistant (sync runs automatically on startup).

**Webhook calls failing**
Check that Home Assistant is reachable from the machine running Marinara Engine. If they're on the same host, the internal URL (`http://localhost:8123`) is used automatically.

**Cannot connect on setup**
Make sure Marinara Engine is running (`pnpm dev` or the packaged app) and the host/port match what you entered.
