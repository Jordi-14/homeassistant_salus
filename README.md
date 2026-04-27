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

Version `0.6.0` switches the integration from the unmaintained `pyit600`
dependency to `salus-it600-client==0.1.0`. Existing Home Assistant config
entries continue to use the same `salus` integration domain, so normal HACS
updates should only require a restart.

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
- covers: RS600

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

This is a local polling integration. Gateway data is refreshed every 10 seconds
through one shared coordinator, then reused by all entity platforms.

## Troubleshooting

If the EUID printed on the gateway does not work, try `0000000000000000`.

Check that Local WiFi Mode is enabled:

1. Open the Salus Smart Home app.
2. Sign in.
3. Double tap the gateway to open the info screen.
4. Open the gateway settings.
5. Confirm `Disable Local WiFi Mode` is set to `No`.
6. Save settings.
7. Power-cycle the gateway.

## Removal

1. Remove the `Salus iT600` integration from `Settings -> Devices & services`.
2. If installed through HACS, uninstall it from HACS.
3. Restart Home Assistant.

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
