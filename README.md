# Salus iT600 for Home Assistant

Custom Home Assistant integration for local control and monitoring of Salus
iT600 devices through a Salus gateway with Local WiFi Mode enabled.

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

## Development And Testing

Contributor documentation lives in [CONTRIBUTING.md](CONTRIBUTING.md).
It covers:

- architecture and platform layout;
- adding new entity platforms;
- local quality checks;
- testing integration, client, and coordinated feature branches before release;
- SQ610 implementation notes.

Release publishing is documented in [RELEASE.md](RELEASE.md).
Archived upstream issue notes for future maintenance live in
[docs/upstream-issues.md](docs/upstream-issues.md).

## Maintenance Notes

This fork uses `salus-it600-client`, a maintained successor of the original
`pyit600` library. The package was renamed to avoid conflicts with the
unmaintained `pyit600` distribution while preserving the original MIT license
and attribution.

Gateway protocol handling, payload compatibility, commands, and device models
live in `salus-it600-client`. This integration keeps the Home Assistant config
flow, coordinator, and entity platform code.

## Project Origin

This repository is a fork of `https://github.com/epoplavskis/homeassistant_salus`,
which is a fork of `https://github.com/konradb3/homeassistant_salus`.

The maintained fork also incorporates and reworks feature ideas from Leonard
Pitzu's `https://github.com/leonardpitzu/homeassistant_salus` fork, including
broader device coverage, UG800/new-firmware support, TRV-related entities,
SQ610-related improvements, smart-plug metering, and thermostat lock support.

The current structure keeps those protocol and parsing improvements in the
reusable `salus-it600-client` package where possible, while this repository
exposes them through Home Assistant entities, diagnostics, options, repairs,
translations, and release metadata.
