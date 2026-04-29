# Release Process

This repository publishes a Home Assistant custom integration through GitHub
Releases and HACS. The integration depends on the separate
`salus-it600-client` Python package.

## Policy

`master` is the release branch. Keep it stable and releasable.

Do not release an integration version that points at an unpublished client
package. Home Assistant installs dependencies from
`custom_components/salus/manifest.json`, so the pinned `salus-it600-client`
version must already be available on PyPI.

The practical invariant is:

- the latest HACS release must correspond to a `vX.Y.Z` tag on `master`;
- `custom_components/salus/manifest.json` contains the released integration
  version;
- the manifest pins a published `salus-it600-client` version;
- unreleased work happens on feature branches.

## Normal Development

1. Start from `master`.
2. Create a feature or fix branch.
3. Make the code change and add tests.
4. Run the local checks from [CONTRIBUTING.md](CONTRIBUTING.md).
5. For user-facing behavior, test the branch with Home Assistant using
   [CONTRIBUTING.md](CONTRIBUTING.md).
6. If the integration needs unreleased client behavior, test both branches
   together before merge.
7. Open and merge the branch into `master` after CI passes.

## Coordinated Client Releases

When the integration requires client changes:

1. Merge and publish the `salus-it600-client` release first.
2. Confirm the intended client version is available on PyPI.
3. Update `custom_components/salus/manifest.json` to pin that exact client
   version.
4. Run the integration checks again.
5. Test the integration branch in Home Assistant before merging or releasing.

## Publishing

After merging the release commit to `master`:

```bash
git switch master
git pull --ff-only origin master
python3 -m json.tool custom_components/salus/manifest.json > /dev/null
python3 -m json.tool custom_components/salus/strings.json > /dev/null
python3 -m json.tool custom_components/salus/translations/en.json > /dev/null
python3 -m json.tool custom_components/salus/translations/ca.json > /dev/null
python3 -m unittest discover -q
python3 -m ruff check custom_components tests
python3 -m compileall -q custom_components tests
git tag vX.Y.Z
git push origin vX.Y.Z
```

Create the GitHub Release from the tag. HACS uses the GitHub Release and the
integration version in `manifest.json` to offer updates.

## Release Checklist

1. Test feature branches before merge when the change is user-facing or depends
   on unreleased client behavior. Use [CONTRIBUTING.md](CONTRIBUTING.md).
2. Run the `salus-it600-client` test suite and coverage report when the client
   changed.
3. Publish the intended `salus-it600-client` version to PyPI when the client
   changed.
4. Update `custom_components/salus/manifest.json` to pin the published client
   version.
5. Run the Home Assistant integration compile and test checks.
6. Tag and release `homeassistant_salus`.
7. Install or update the released integration through HACS on a real Home
   Assistant instance.
8. Reload the config entry and verify one gateway poll plus one safe command on
   a real Salus gateway.
9. Check Home Assistant release notes for integration API deprecations affecting
   config entries, entity platforms, diagnostics, or manifest metadata.
