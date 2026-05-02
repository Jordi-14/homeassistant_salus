# Salus iT600 for Home Assistant

A custom [Home Assistant](https://www.home-assistant.io/) integration that lets you control and monitor your [Salus iT600](https://salus-controls.com/) smart home devices **locally** through the UGE600 or UG800 gateway — thermostats, smart plugs, roller shutters, sensors, and more, all without cloud dependency.

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
| **Low battery** | Battery warning for wireless sensors and TRVs (it600MINITRV via TRVError22) |
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
3. Enter your gateway's **IP address** and **EUID**.
4. The integration will discover all devices on the gateway and create entities automatically.

### Finding the EUID

The EUID is a 16-character hexadecimal string printed on the bottom of the gateway, under the micro-USB port. For example: `001E5E0D32906128`.

If the printed EUID does not work, try `0000000000000000` — some gateways accept a zeroed EUID instead of the physical one.

### Data updates

This is a local polling integration. Gateway data is refreshed every 20 seconds by default through one shared coordinator, then reused by all entity platforms. The regular poll interval is configurable in integration options.

After a Home Assistant command (e.g. changing a thermostat target temperature or turning on a switch), the integration requests one verification refresh after 5 s by default. This delay is configurable in integration options.

## Supported devices

| Category | Devices |
|---|---|
| **Climate** | HTRP-RF(50), TS600, VS10WRF/VS10BRF, VS20WRF/VS20BRF, SQ610, SQ610RF, FC600, TRV3RF, it600MINITRV |
| **Binary sensors** | SW600, WLS600, OS600, SD600, TRV10RFM, RX10RF, SmokeSensor-EM |
| **Temperature sensors** | PS600 |
| **Switches** | SP600, SPE600 |
| **Covers** | RS600, SR600 |
| **Locks** | Any thermostat with child-lock support |

Known unsupported: SB600, CSB600 (button actions only work through the Salus Smart Home app).

### SQ610 notes

The SQ610 Quantum thermostat has additional handling:

- Heat and Cool mode exposure
- Direct standby handling via `HoldType`
- Simplified preset controls: `Permanent Hold`, `Standby`, and `Follow Schedule`
- Humidity reading from the `SunnySetpoint_x100` register
- Floor temperature from external probe (`OUTSensorProbe`)

Selecting **Follow Schedule** returns the thermostat to the schedule configured in the Salus Smart Home app.

## Troubleshooting

- If the gateway IP or EUID changes, use **Reconfigure** from the integration entry menu — no need to delete and recreate.
- Make sure **Local WiFi Mode** is enabled on your gateway:
  1. Open the Salus Smart Home app on your phone and sign in.
  2. Double-tap your gateway to open the info screen.
  3. Press the gear icon to enter configuration.
  4. Scroll down and check that **Disable Local WiFi Mode** is set to **No**.
  5. Scroll to the bottom, save settings, and restart the gateway by unplugging/plugging USB power.
- If polling fails repeatedly, Home Assistant creates a **Repairs** issue linking back to this section. The repair clears automatically after the gateway responds successfully again.

### Debugging

If you're having issues with the integration, there are two ways to enable debug logging.

**Option 1 — YAML configuration**

Add the following to your `configuration.yaml` and restart Home Assistant:

```yaml
logger:
  default: info
  logs:
    custom_components.salus: debug
```

**Option 2 — Home Assistant UI**

1. Go to **Settings** → **Devices & Services**.
2. Find the **Salus iT600** integration and click the **⋮** menu.
3. Select **Enable debug logging**.
4. Reproduce the issue.
5. Click **Disable debug logging** — the browser will download a log file you can inspect or attach to a bug report.

This method is useful for one-off troubleshooting since it automatically reverts to the normal log level once you stop it.

### Diagnostics

1. Open **Settings** → **Devices & Services**.
2. Select the **Salus iT600** integration.
3. Open the three-dot menu → **Download diagnostics**.

Diagnostics include integration version, gateway health counters, device counts, availability history, and SQ610 support fields. The gateway EUID/token is redacted automatically.

Review the file before posting publicly — it may contain your gateway IP and device IDs.

For support requests, include:

- Home Assistant version
- `homeassistant_salus` version
- `salus-it600-client` version (from `custom_components/salus/manifest.json`)
- Gateway model (UGE600 or UG800) if known
- Whether the gateway uses legacy or newer firmware if known
- Diagnostics file or the relevant redacted snippets
- Home Assistant logs around startup, reload, polling, or the failed command

## Encryption & protocol support

Salus gateways encrypt all local API traffic. Different gateway models and firmware versions use different encryption protocols. The integration **auto-detects** the correct protocol by trying each one in order during connection.

| | Legacy AES-CBC | AES-CCM (newer firmware) |
|---|---|---|
| **Gateways** | UGE600, older UG800 firmware | UG800 with newer firmware |
| **Cipher** | AES-256-CBC (fallback: AES-128-CBC) | AES-256-CCM (authenticated encryption) |
| **Key derivation** | `MD5("Salus-{euid}")` — static, derived from the gateway EUID | EUID bytes + hardcoded suffix — 32-byte key derived from the gateway EUID |
| **IV / nonce** | Fixed 16-byte IV | 8-byte random nonce (3 random + 2-byte counter + 3-byte timestamp) |
| **Authentication** | None | 8-byte MAC tag (CBC-MAC) |
| **Padding** | PKCS7 | None (CCM handles arbitrary lengths) |
| **Wire format** | Block-aligned encrypted HTTP body | `[ciphertext + 8-byte MAC][8-byte nonce]` |

Protocol auto-detection order:
1. **AES-256-CBC** — legacy iT600 / UGE600 gateways
2. **AES-128-CBC** — intermediate firmware variant
3. **AES-CCM** — newer UG800 firmware

A rejected attempt is identified by a characteristic 33-byte reject frame (trailer byte `0xAE`).

For full protocol implementation details, see the [`salus-it600-client`](https://github.com/Jordi-14/salus-it600-client) library documentation.

## Development and testing

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture, testing, and platform development details.

Release publishing is documented in [RELEASE.md](RELEASE.md).

## Migration from `pyit600`

This integration uses `salus-it600-client`, a maintained successor of the original `pyit600` library. Existing Home Assistant config entries keep the same `salus` integration domain, so normal HACS updates only require a restart.

The exact client version is pinned in `custom_components/salus/manifest.json`.

## Project origin

This repository is a fork of [`epoplavskis/homeassistant_salus`](https://github.com/epoplavskis/homeassistant_salus), which is a fork of [`konradb3/homeassistant_salus`](https://github.com/konradb3/homeassistant_salus).

It incorporates and reworks feature ideas from Leonard Pitzu's [`leonardpitzu/homeassistant_salus`](https://github.com/leonardpitzu/homeassistant_salus) fork, including broader device coverage, UG800/new-firmware support, TRV-related entities, SQ610 improvements, smart-plug metering, and thermostat lock support.

Protocol and parsing logic lives in the reusable [`salus-it600-client`](https://github.com/Jordi-14/salus-it600-client) library. This repository exposes those capabilities through Home Assistant entities, diagnostics, options, repairs, and translations.

## License

Licensed under the Apache License, Version 2.0 — see [LICENSE](LICENSE) for details.
