# Changelog

## 0.9.0 - 2026-05-23

Device support:

- Require `salus-it600-client 0.6.0`.
- Add SQ610 Away preset support.
- Show SQ610 and FC600 `Schedule Override` only while the device reports an
  active schedule override.
- Keep `Schedule Override` as a reported state instead of a normal selectable
  preset.

## 0.8.2 - 2026-05-22

Polish:

- Improve generated entity names so Home Assistant can use device-level naming
  consistently across Salus entities.
- Add localized entity-name strings for English and Catalan.
- Add migration guidance, supported-device documentation, and GitHub issue/PR
  templates.

## 0.8.1 - 2026-05-08

Best-practice hardening:

- Require `salus-it600-client 0.5.1`.
- Reuse Home Assistant's shared aiohttp client session for gateway setup and
  config-flow validation so gateway HTTP connections follow Home Assistant's
  session lifecycle.
- Modernize options-flow and runtime-data typing by using
  `ConfigEntry[SalusRuntimeData]` and Home Assistant's `self.config_entry`
  options-flow property.
- Set the Salus data coordinator to `always_update=False` and add regression
  coverage so unchanged snapshots do not dispatch redundant entity updates.

## 0.8.0 - 2026-05-04

Normalized climate model:

- Require `salus-it600-client 0.5.0`.
- Consume normalized climate fields from `salus-it600-client` for SQ610, FC600,
  TRV, and standard thermostat state instead of doing a second raw SQ610 detail
  fetch during normal polling.
- Keep heat/cool target temperature and active range selection aligned with the
  normalized client model, including cooling states proven by running state.
- Report climate diagnostics through one shared climate-device diagnostics
  shape, with normalized fields and whitelisted support fields for every
  thermostat family.

## 0.7.22 - 2026-05-03

Bug fixes:

- Require `salus-it600-client 0.4.9` so SQ610/SQ610NH thermostats expose
  keypad lock entities and use the SQ610 lock write path.
- Include SQ610 `LockKey` and `LockKey_a` values in diagnostics support fields.

## 0.7.21 - 2026-05-03

Device support:

- Require `salus-it600-client 0.4.8` for RS600/SR600 multifunction mapping.
- Group RS600/SR600 switch endpoint entities under the base Home Assistant
  device identifier so relay switches and the RS600 cover appear on one device.
- Treat SR600 as a dry relay switch rather than a cover and document how users
  should disable unused RS600 cover or switch representations.

## 0.7.20 - 2026-05-03

Device support:

- Require `salus-it600-client 0.4.7` for ECM600 energy meter support, exposing
  per-endpoint power, energy, and diagnostic battery sensors.
- Pick up the client-side FC600 variant handling so models such as `FC600NH`
  use the same fan-coil parsing and write-command paths as `FC600`.

## 0.7.17 - 2026-05-02

Bug fixes:

- Require `salus-it600-client 0.4.6` so FC600 fan mode writes use the local
  gateway payload accepted by the official Salus app.

## 0.7.11 - 2026-04-29

Polish:

- Require `salus-it600-client 0.4.4`.
- Mark RS600/SR600 covers as shutters for better Home Assistant UI display.
- Add state classes for battery, humidity, power, temperature, and energy
  sensors so they can participate in Home Assistant long-term statistics.
- Refresh README examples that still referenced older client versions.

## 0.7.9 - 2026-04-29

Translations:

- Add Catalan translations for the Home Assistant configuration, options,
  Repairs UI, and SQ610 preset labels.

## 0.7.8 - 2026-04-29

Options UI polish:

- Render polling options as Home Assistant number input selectors instead of
  awkward raw numeric controls.
- Change the default post-command settle refresh delay from 3 seconds to
  4 seconds.

## 0.7.7 - 2026-04-29

User experience:

- Increase normal gateway polling to 20 seconds.
- Keep a fast post-command refresh at 0.5 seconds and add a configurable settle
  refresh, defaulting to 3 seconds, so command changes are rechecked after the
  gateway has had time to update.

## 0.7.6 - 2026-04-29

P3 command reliability:

- Require `salus-it600-client 0.4.3`, which retries a transient gateway server
  disconnect once for encrypted write requests.

## 0.7.5 - 2026-04-29

Bug fixes:

- Convert Salus gateway command connection failures into Home Assistant service
  errors instead of raw websocket tracebacks.

## 0.7.4 - 2026-04-29

Bug fixes:

- Fix the Home Assistant options/reconfigure flow crashing with
  `Config flow could not be loaded` on newer Home Assistant versions.
- Move EUID validation out of the displayed form schema so Home Assistant can
  serialize the config flow form.
- Store the options config entry privately because Home Assistant now exposes
  `config_entry` as a read-only property on options flows.

## 0.7.3 - 2026-04-29

P3 product quality:

- Add reconfigure and reauthentication flows for updating gateway IP/EUID
  without deleting the integration.
- Add a Home Assistant Repairs issue for persistent gateway poll failures, with
  troubleshooting guidance and automatic cleanup after recovery.
- Improve troubleshooting documentation around reconfigure, Local WiFi Mode, and
  the all-zero EUID fallback.

## 0.7.2 - 2026-04-29

P2 maintainability:

- Use semantic SQ610 client write methods from the Home Assistant climate entity
  instead of passing raw gateway property names from the integration layer.
- Add command tests for the SQ610 setpoint, HVAC mode, preset, and turn-off
  paths.
- Add a release checklist step for Home Assistant API deprecation review.
- Require `salus-it600-client 0.4.2`.

## 0.7.1 - 2026-04-29

P1 near-term hardening:

- Document Home Assistant diagnostics download and what to include in support
  requests.
- Add a GitHub issue form for Home Assistant support reports.

P0 release hardening for the current tested pair:

- `homeassistant_salus 0.7.0`
- `salus-it600-client 0.4.0`

Changes:

- Close the Salus gateway client when a config entry unloads successfully.
- Close the Salus gateway client if setup fails after the gateway object has
  been created.
- Add unit tests for gateway lifecycle cleanup during setup failure and unload.
- Run the fast unit test suite in the validation workflow before compile,
  Hassfest, and HACS checks.

Manual release verification still required before tagging:

- Install or update the integration through HACS on a real Home Assistant
  instance.
- Reload the config entry and confirm the gateway session is recreated cleanly.
- Run one read-only gateway poll and one safe command against a real gateway.
