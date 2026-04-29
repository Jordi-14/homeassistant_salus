# Changelog

## Unreleased

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
