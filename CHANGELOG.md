# Changelog

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
