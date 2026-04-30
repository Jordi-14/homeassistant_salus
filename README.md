# Salus iT600 for Home Assistant

A custom [Home Assistant](https://www.home-assistant.io/) integration that lets you control and monitor your [Salus iT600](https://salus-controls.com/) smart home devices **locally** through the UGE600 or UG800 gateway — thermostats, smart plugs, roller shutters, sensors, and more, all without cloud dependency.

This fork is maintained at [`https://github.com/Jordi-14/homeassistant_salus`](https://github.com/Jordi-14/homeassistant_salus).

## Features

### Climate

One climate entity per thermostat connected to the gateway. Two thermostat families are supported:

- **iT600 thermostats** (e.g. SQ610RF) — heat/off/auto modes, Follow Schedule / Permanent Hold / Off presets, current & target temperature, humidity, 0.5 °C increments.
- **FC600 fan-coil controllers** — heat/cool/auto modes, five presets (Follow Schedule, Permanent Hold, Temporary Hold, Eco, Off), fan modes (auto/high/medium/low/off), separate heating/cooling setpoints.

### Sensors

| Sensor | Description |
|---|---|
| **Temperature** | Current temperature reading (°C) |
| **Humidity** | Relative humidity (%) |
| **Battery** | Battery level for wireless thermostats and standalone sensors (%) |
| **Power** | Instantaneous power draw from smart plugs (W) |
| **Energy** | Cumulative energy consumption from smart plugs (kWh) |

### Binary sensors

| Binary sensor | Description |
|---|---|
| **Window / Door** | Open/closed state (SW600, OS600) |
| **Water leak** | Moisture detection (WLS600) |
| **Smoke** | Smoke alarm (SmokeSensor-EM) |
| **Low battery** | Battery warning for wireless sensors and TRVs |
| **Thermostat problem** | Aggregated thermostat error flags with human-readable descriptions as attributes |
| **Battery problem** | Battery-specific thermostat error indicator |

### Covers

One cover entity per roller shutter or blind (SR600, RS600). Supports **open**, **close**, and **set position** (0–100 %).

### Switches

One switch entity per smart plug or relay (SP600, SPE600). Supports **on/off** control. Double-switch devices are exposed as separate entities.

### Locks

One lock entity per thermostat that supports child lock. Allows **locking/unlocking** the thermostat keypad.

## Installation

Minimum supported Home Assistant version: `2024.8.0`.

### HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** → **⋮** → **Custom repositories**.
3. Add `https://github.com/Jordi-14/homeassistant_salus` as an **Integration**.
4. Search for **Salus iT600** and install it.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/salus` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **Salus iT600**.
3. Enter your gateway's **IP address** and **EUID** (the first 16 characters printed under the gateway's micro-USB port).
4. The integration will discover all devices on the gateway and create entities automatically.

Data is polled every 20 seconds. All communication is local over your LAN. After a command (e.g. changing a thermostat target temperature), the integration requests a fast refresh after 0.5 s and a settle refresh after 4 s (configurable in integration options).

## Supported devices

| Category | Devices |
|---|---|
| **Climate** | HTRP-RF(50), TS600, VS10WRF/VS10BRF, VS20WRF/VS20BRF, SQ610, SQ610RF, FC600 |
| **Binary sensors** | SW600, WLS600, OS600, SD600, TRV10RFM, RX10RF |
| **Temperature sensors** | PS600 |
| **Switches** | SPE600, RS600, SR600 |
| **Covers** | RS600, SR600 |

Known unsupported: SB600, CSB600.

## Troubleshooting

- If you can't connect using the EUID on your gateway (e.g. `001E5E0D32906128`), try `0000000000000000` as EUID.
- If the gateway IP or EUID changes, use **Reconfigure** from the integration entry menu — no need to delete and recreate.
- Make sure **Local WiFi Mode** is enabled on your gateway:
  1. Open the Salus Smart Home app on your phone and sign in.
  2. Double-tap your gateway to open the info screen.
  3. Press the gear icon to enter configuration.
  4. Scroll down and check that **Disable Local WiFi Mode** is set to **No**.
  5. Scroll to the bottom, save settings, and restart the gateway by unplugging/plugging USB power.

### Debug logging

Add the following to your `configuration.yaml` and restart Home Assistant:

```yaml
logger:
  default: info
  logs:
    custom_components.salus: debug
```

Or use the UI: **Settings** → **Devices & Services** → find **Salus iT600** → **⋮** → **Enable debug logging**.

### Diagnostics

1. Open **Settings** → **Devices & Services**.
2. Select the **Salus iT600** integration.
3. Open the three-dot menu → **Download diagnostics**.

The gateway EUID/token is redacted automatically. Review the file before posting publicly as it may contain your gateway IP and device IDs.

## Development and testing

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture, testing, and platform development details.

Release publishing is documented in [RELEASE.md](RELEASE.md).

## Project origin

This repository is a fork of [`epoplavskis/homeassistant_salus`](https://github.com/epoplavskis/homeassistant_salus), which is a fork of [`konradb3/homeassistant_salus`](https://github.com/konradb3/homeassistant_salus).

It also incorporates and reworks feature ideas from Leonard Pitzu's [`leonardpitzu/homeassistant_salus`](https://github.com/leonardpitzu/homeassistant_salus) fork, including broader device coverage, UG800/new-firmware support, TRV-related entities, SQ610 improvements, smart-plug metering, and thermostat lock support.

Protocol and parsing logic lives in the reusable [`salus-it600-client`](https://github.com/Jordi-14/salus-it600-client) library. This repository exposes those capabilities through Home Assistant entities, diagnostics, options, repairs, and translations.

## License

Licensed under the Apache License, Version 2.0 — see [LICENSE](LICENSE) for details.
