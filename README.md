# Salus iT600 for Home Assistant

Custom Home Assistant integration for local control and monitoring of Salus
iT600 devices through a Salus UGE600 gateway.

This fork is maintained at `https://github.com/Jordi-14/homeassistant_salus`.

## Installation

Minimum supported Home Assistant version: `2024.8.0`.

### HACS

1. In HACS, add `https://github.com/Jordi-14/homeassistant_salus` as a custom repository.
2. Select category `Integration`.
3. Install `Salus iT600`.
4. Restart Home Assistant.

### Manual

Copy `custom_components/salus` from this repository to
`/config/custom_components/salus`, then restart Home Assistant.

## Migration Notes

This fork uses the maintained `salus-it600-client` package instead of the
unmaintained `pyit600` dependency. Existing Home Assistant config entries keep
the same `salus` integration domain, so normal HACS updates should only require
a restart.

The exact client version is pinned in `custom_components/salus/manifest.json`.
The current tested integration line uses `salus-it600-client==0.4.4`.

Custom Python code outside this integration that imports `pyit600` should be
updated to import from `salus_it600` instead.

## Configuration

1. In Home Assistant, go to `Settings -> Devices & services`.
2. Select `Add Integration`.
3. Search for `Salus iT600`.
4. Enter the gateway IP address and the first 16 characters of the gateway EUID.

The EUID is normally printed on the bottom of the gateway under the microUSB
port, for example `001E5E0D32906128`.

## Supported Devices

Device support comes from the underlying `salus-it600-client` library.

Known supported categories:

- climate devices: HTRP-RF(50), TS600, VS10WRF/VS10BRF, VS20WRF/VS20BRF, SQ610, SQ610RF, FC600
- binary sensors: SW600, WLS600, OS600, SD600, TRV10RFM, RX10RF
- temperature sensors: PS600
- switches: SPE600, RS600, SR600
- covers: RS600, SR600

Known unsupported devices:

- SB600
- CSB600

Some devices may expose only a subset of their native Salus features through the local gateway API.

## SQ610 Notes

This fork includes additional SQ610 Quantum thermostat handling:

- Heat and Cool mode exposure in Home Assistant
- direct standby handling
- simplified preset controls: `Permanent Hold`, `Standby`, and `Follow Salus Schedule`

Selecting `Follow Salus Schedule` returns the thermostat to the schedule
configured in the Salus app.

## Data Updates

This is a local polling integration. Gateway data is refreshed every 20 seconds
through one shared coordinator, then reused by all entity platforms.

After a Home Assistant command, such as changing a thermostat target
temperature or turning on a switch, the integration requests an additional fast
refresh after 0.5 seconds and a second settle refresh after 4 seconds by default.
The settle refresh delay can be changed from the integration options.

## Troubleshooting

If the gateway IP address or EUID changes, open the integration entry from
`Settings -> Devices & services -> Salus iT600` and use `Reconfigure` from the
entry menu. You do not need to delete and recreate the integration just to
change the connection settings.

If the EUID printed on the gateway does not work, try `0000000000000000`.

Check that Local WiFi Mode is enabled:

1. Open the Salus Smart Home app.
2. Sign in.
3. Double tap the gateway to open the info screen.
4. Open the gateway settings.
5. Confirm `Disable Local WiFi Mode` is set to `No`.
6. Save settings.
7. Power-cycle the gateway.

If polling fails repeatedly, Home Assistant creates a Repairs issue linking
back to this troubleshooting section. The repair clears automatically after the
gateway responds successfully again.

### Diagnostics For Support

Home Assistant diagnostics are useful when reporting gateway, device, or SQ610
issues:

1. Open `Settings -> Devices & services`.
2. Select the `Salus iT600` integration.
3. Open the three-dot menu for the config entry.
4. Select `Download diagnostics`.

Diagnostics include integration version, gateway health counters, device counts,
availability history, and reduced SQ610 support fields. The gateway EUID/token
is redacted automatically. The gateway host/IP address and Salus device IDs may
still be present, so review the file before posting it publicly.

For support requests, include:

- Home Assistant version
- `homeassistant_salus` version
- `salus-it600-client` version from `custom_components/salus/manifest.json`
- gateway model if known
- whether the gateway uses UG600/legacy firmware or UG800/newer firmware if known
- diagnostics file or the relevant redacted snippets
- Home Assistant logs around startup, reload, polling, or the failed command

## Removal

1. Remove the `Salus iT600` integration from `Settings -> Devices & services`.
2. If installed through HACS, uninstall it from HACS.
3. Restart Home Assistant.

## Architecture Overview

This integration uses the **DataUpdateCoordinator** pattern to poll the Salus gateway every 20 seconds and share device snapshots with all entity platforms:

```
Home Assistant Setup
    ↓
config_flow.py: User enters gateway IP + EUID
    ↓
__init__.py: Connects to gateway, creates coordinator + runtime_data
    ↓
coordinator.py (DataUpdateCoordinator)
    ├─ Every 20 seconds:
    │  ├─ gateway.poll_status() ← Fetches all device types
    │  ├─ Extract devices by type (climate, binary_sensor, switch, etc.)
    │  ├─ SQ610 raw props fetch (protocol quirk workaround)
    │  └─ Notify all listeners with new SalusData snapshot
    ├─ Error handling:
    │  ├─ Auth error → ConfigEntryAuthFailed (won't retry)
    │  └─ Connection error → UpdateFailed (coordinator retries)
    │
    └─ Platforms (climate, switch, binary_sensor, cover, sensor)
        ├─ Subscribe to coordinator updates
        ├─ Create SalusEntity subclasses for each device
        ├─ Read device state from coordinator.data[device_id]
        └─ Call gateway methods for control (set_temperature, turn_on, etc.)
```

**Key Design Decisions:**
- **Single polling source:** All platforms read from same coordinator → consistent state
- **Gateway lock:** asyncio.Lock prevents concurrent requests during polling
- **Immutable snapshots:** Each update creates new SalusData dict (thread-safe)
- **Entity discovery:** New devices appear in UI automatically via coordinator callbacks

## Integration Structure

| Module | Purpose |
|--------|---------|
| `config_flow.py` | Validates EUID, tests gateway connection, creates config entry |
| `__init__.py` | Sets up coordinator, registers gateway device, forwards platforms |
| `coordinator.py` | Polls gateway every 20s, aggregates device data, notifies platforms |
| `entity.py` | Base entity class, device registry pattern, entity factory helper |
| `climate.py` | Thermostat entities, SQ610 special handling, mode/preset mapping |
| `switch.py` | Relay/switch entities, on/off control |
| `binary_sensor.py` | Door/window sensors, state interpretation |
| `cover.py` | Blind/shutter entities, position control |
| `sensor.py` | Temperature/humidity/power/energy sensors, state and statistics mapping |
| `lock.py` | Thermostat keypad lock entities |
| `const.py` | Constants (polling interval, platforms, domain) |
| `strings.json` | Translatable strings for config flow UI |

## Adding a New Device Platform

If you want to support a new device type (e.g., `light`, `lock`), follow these steps:

### Step 1: Identify if salus-it600-client Supports the Device

Check `salus-it600-client/salus_it600/device_models.py` to see if the device model is listed. If not:
1. Update `salus-it600-client` first to add device parsing
2. Then return to add the Home Assistant platform

### Step 2: Create the Platform Module

Create `custom_components/salus/<platform>.py`:

```python
\"\"\"Support for Salus <device type>.\"\"\"

from homeassistant.components.<platform> import <PlatformEntity>
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SalusData, SalusRuntimeData
from .entity import SalusEntity, async_add_salus_entities

_LOGGER = logging.getLogger(__name__)

class Salus<PlatformEntity>(SalusEntity, <PlatformEntity>):
    \"\"\"Salus <device type> entity.\"\"\"

    @property
    def _device(self):
        \"\"\"Return current device from coordinator.data.\"\"\"
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.<platform>_devices.get(self._device_id)

    # Implement platform-specific properties and methods
    # Example for light:
    #   @property
    #   def is_on(self) -> bool:
    #       return bool(self._device.state)
    #
    #   async def async_turn_on(self, **kwargs) -> None:
    #       await self.coordinator.hass.config_entries.runtime_data.gateway.\\
    #           set_switch_device_state(self._device_id, True)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    \"\"\"Set up Salus <device type> from a config entry.\"\"\"
    runtime_data: SalusRuntimeData = config_entry.runtime_data
    coordinator = runtime_data.coordinator

    async_add_salus_entities(
        config_entry,
        coordinator,
        async_add_entities,
        entity_factory=lambda device_id: Salus<PlatformEntity>(coordinator, device_id),
        devices_getter=lambda data: data.<platform>_devices,
    )
```

### Step 3: Register Platform in Manifest

Edit `custom_components/salus/manifest.json`:

```json
{
  "version": "...",
  "domain": "salus",
  "codeowners": ["@Jordi-14"],
  "config_flow": true,
  "documentation": "https://github.com/Jordi-14/homeassistant_salus",
  "homeassistant": "2024.8.0",
  "iot_class": "local_polling",
  "requirements": ["salus-it600-client==0.4.4"],
  "platforms": ["binary_sensor", "climate", "cover", "lock", "sensor", "switch", "<new_platform>"]
}
```

### Step 4: Update Integration Constants

Edit `custom_components/salus/const.py`:

```python
PLATFORMS: tuple[Platform, ...] = (
    Platform.CLIMATE,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.COVER,
    Platform.SENSOR,
    Platform.<NEW_PLATFORM>,  # Add here
)
```

### Step 5: Add Platform to Setup

Edit `custom_components/salus/__init__.py` (no changes needed if you already added to PLATFORMS):

The `async_forward_entry_setups()` call automatically discovers all platforms listed in PLATFORMS.

### Step 6: Add Tests

Create `tests/test_<platform>.py` with:
- Coordinator snapshot tests (device data conversion)
- Entity property tests (state mapping)
- Command tests (call gateway methods correctly)

## Developing Locally

### Running Tests

```bash
cd homeassistant_salus
python3 -m unittest discover -q
python3 -m ruff check custom_components tests
python3 -m compileall -q custom_components tests
```

### Testing with a Real Gateway

1. Install Home Assistant Development environment (Core)
2. Copy integration to your Home Assistant config: `cp -r custom_components/salus ~/.homeassistant/custom_components/`
3. Add to `configuration.yaml`:
   ```yaml
   # Disable if using UI config entries
   # salus:
   #   host: 192.168.1.100
   #   token: "001E5E0D32906128"
   ```
4. Restart Home Assistant
5. Go to Settings → Devices & Services → Add Integration → Search "Salus"

### Pre-commit Hooks

Install linters to catch issues early:

```bash
pip install pre-commit
pre-commit install
```

Pre-commit config (add to `.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.12
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

## SQ610 Quantum Thermostat Notes

SQ610 thermostats require special handling due to unusual protocol quirks:

### Humidity Field Quirk

SQ610 doesn't report humidity through the standard field. Instead, humidity is stored in `SunnySetpoint_x100`:

```python
# salus-it600-client handles this automatically:
if is_sq610_model(device.model):
    humidity = device.humidity  # Populated from SunnySetpoint_x100 by library
```

### Dual Setpoints

SQ610 has separate heating and cooling setpoints. Which one is used depends on system mode:

```python
# Selected automatically by library based on SystemMode
if system_mode == "heat":
    target = heating_setpoint
elif system_mode == "cool":
    target = cooling_setpoint
```

### Preset Handling

This integration simplifies SQ610 presets to three options:

- **Permanent Hold**: Keep current setpoint indefinitely
- **Standby**: Turn off (gateway returns device to standby mode)
- **Follow Salus Schedule**: Return to weekly schedule configured in Salus app

### Raw Properties Fetch

The coordinator makes an extra encrypted request to fetch SQ610 raw payload fields. These are stored in `coordinator.data.raw_climate_props[device_id]` and provide access to fields not exposed by the `salus-it600-client` library. This is non-blocking: if it fails, the integration continues normally with cached values.

## Maintenance Notes

This fork uses `salus-it600-client`, a maintained successor of the original
`pyit600` library. The package was renamed to avoid conflicts with the
unmaintained `pyit600` distribution while preserving the original MIT license
and attribution.

Gateway protocol handling, payload compatibility, commands, and device models
live in `salus-it600-client`. This integration keeps the Home Assistant config
flow, coordinator, and entity platform code.

## Code Origin

This repository is a fork of `https://github.com/epoplavskis/homeassistant_salus`,
which is a fork of `https://github.com/konradb3/homeassistant_salus`.
