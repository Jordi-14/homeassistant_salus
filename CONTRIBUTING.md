# Contributing

This document covers development, testing, and pull-request preparation for
`homeassistant_salus`.

Public repositories:

- Home Assistant integration: `https://github.com/Jordi-14/homeassistant_salus`
- Client package: `https://github.com/Jordi-14/salus-it600-client`

End-user installation, setup, troubleshooting, and diagnostics guidance live in
[README.md](README.md). Release policy lives in [RELEASE.md](RELEASE.md).
Historical upstream issue notes live in
[docs/upstream-issues.md](docs/upstream-issues.md).

## Repository Boundary

This repository contains the Home Assistant custom integration:

- config flow and options flow;
- DataUpdateCoordinator setup;
- entity platforms;
- diagnostics, repairs, translations, and Home Assistant UX.

Gateway protocol parsing, encryption, device models, and low-level commands
belong in `salus-it600-client`. If a Home Assistant change needs raw gateway
fields or a new command payload, add a public client method first and consume
that method here.

## Fork Workflow

If you do not have permission to push branches to `Jordi-14/homeassistant_salus`,
fork the repository and push your feature branch to your fork. Open the pull
request back to `Jordi-14/homeassistant_salus`.

The branch-testing examples use owner placeholders:

- `<integration-owner>`: `Jordi-14` for maintainers, or your GitHub username for
  integration fork branches.
- `<client-owner>`: `Jordi-14` for maintainers, or your GitHub username for
  client fork branches.

## Local Checks

Run these before opening a pull request:

```bash
python3 -m json.tool custom_components/salus/manifest.json > /dev/null
python3 -m json.tool custom_components/salus/strings.json > /dev/null
python3 -m json.tool custom_components/salus/translations/en.json > /dev/null
python3 -m json.tool custom_components/salus/translations/ca.json > /dev/null
python3 -m unittest discover -q
python3 -m ruff check custom_components tests
python3 -m compileall -q custom_components tests
```

When changing UI text, update `strings.json` and all translation files. Logs,
diagnostics internals, and developer-only messages can stay in English.

## Architecture

The integration uses one `DataUpdateCoordinator` to poll the Salus gateway every
20 seconds and share one device snapshot across all platforms:

```text
config_flow.py
  -> __init__.py creates gateway and coordinator
  -> coordinator.py polls salus-it600-client
  -> SalusData snapshot
  -> climate, switch, binary_sensor, cover, sensor, lock entities
```

Key rules:

- All entity platforms read from the coordinator snapshot.
- Gateway commands go through public `IT600Gateway` methods.
- New device parsing belongs in `salus-it600-client`, not in entity classes.
- Entity classes should adapt client models to Home Assistant behavior.

## Adding Or Changing Entity Support

1. Confirm the device model and behavior are already supported by
   `salus-it600-client`.
2. If client support is missing, implement and release the client change first.
3. Add or update the Home Assistant entity platform.
4. Add tests for entity state, command calls, unavailable behavior, and device
   registry behavior.
5. Update translations when user-facing names, options, repairs, or config-flow
   text changes.

To add a new platform, register it in `custom_components/salus/const.py`:

```python
PLATFORMS: tuple[Platform, ...] = (
    Platform.CLIMATE,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.COVER,
    Platform.SENSOR,
    Platform.LOCK,
    Platform.<NEW_PLATFORM>,
)
```

Use `async_add_salus_entities()` from `entity.py` so discovery behavior stays
consistent across platforms.

## Testing Feature Branches Before Release

Feature branches can be tested in Home Assistant before creating a GitHub
Release, creating a HACS release, or publishing a client package.

General rules:

- Use a non-critical Home Assistant instance when possible.
- Back up `/config/custom_components/salus` before replacing it.
- Restart Home Assistant after changing custom component files, `manifest.json`,
  or Python dependencies. Reloading the config entry is not enough.
- Record the integration branch, client branch, and commit SHA tested.
- Never merge or release a manifest that points to a Git branch, local wheel, or
  other test-only dependency.

### Integration-Only Branch

Use this when the integration changes but the existing published client pin in
`manifest.json` is still correct.

```bash
cd /config
mkdir -p custom_components
if [ -d custom_components/salus ]; then
  mv custom_components/salus custom_components/salus.backup-YYYYMMDDHHMM
fi
git clone --depth 1 --branch <integration-branch> \
  https://github.com/<integration-owner>/homeassistant_salus salus-branch-test
cp -R salus-branch-test/custom_components/salus custom_components/salus
```

Restart Home Assistant and run the real-gateway checklist below.

Roll back with:

```bash
cd /config
rm -rf custom_components/salus
if [ -d custom_components/salus.backup-YYYYMMDDHHMM ]; then
  mv custom_components/salus.backup-YYYYMMDDHHMM custom_components/salus
fi
rm -rf salus-branch-test
```

### Unreleased Client Branch

Use this for Home Assistant OS or another managed environment where you cannot
directly install a local wheel.

First run the client checks from the client feature branch. Then create a
temporary integration test branch and point `custom_components/salus/manifest.json`
at the client branch:

```json
"requirements": [
  "salus-it600-client @ git+https://github.com/<client-owner>/salus-it600-client.git@<client-branch>"
]
```

Push the temporary integration branch, install it manually using the
integration-only branch process, restart Home Assistant, and run the
real-gateway checklist.

Before opening or merging the real integration PR, restore the manifest to a
published PyPI version. After the client package is released, update the
manifest to the published package pin and rerun the local checks.

### Integration And Client Branches Together

Use this when both repositories must be validated together before either PR is
merged.

1. Run the client checks on the client feature branch.
2. Run the integration checks on the integration feature branch.
3. Create a temporary test branch from the integration feature branch.
4. In that temporary branch, set the manifest requirement to the client branch
   using the Git requirement format above.
5. Push the temporary integration branch.
6. Install it manually in the test Home Assistant config.
7. Restart Home Assistant and run the real-gateway checklist.
8. Delete or discard the temporary test branch after testing.

After the client PR is merged and `salus-it600-client` is published, update the
integration branch to pin the published client version and rerun the integration
checks before merging.

## Real-Gateway Checklist

At minimum, verify:

- Home Assistant starts without dependency or custom component errors.
- The Salus config entry reloads cleanly.
- Entities become available after polling.
- One safe command succeeds.
- Post-command refresh behavior updates the UI as expected.
- Diagnostics download works.
- Reconfigure, reauth, Repairs, options, translations, or entity registry
  behavior are tested when the change touches those areas.
- Logs contain no raw tracebacks, dependency install failures, duplicate entity
  warnings, unclosed sessions, or repeated polling failures.

## SQ610 Notes

SQ610 thermostats have special Home Assistant handling for Heat/Cool exposure,
standby, and the simplified presets `Permanent Hold`, `Standby`, and
`Follow Salus Schedule`.

Raw SQ610 protocol behavior belongs in `salus-it600-client`. The integration
should expose Home Assistant concepts and avoid duplicating protocol constants
inside entity classes.
