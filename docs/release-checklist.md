# Release Checklist

1. Run the `salus-it600-client` test suite and coverage report.
2. Publish the intended `salus-it600-client` version to PyPI.
3. Update `custom_components/salus/manifest.json` to pin that exact client version.
4. Run the Home Assistant integration compile and test checks.
5. Tag and release `homeassistant_salus`.
6. Install or update the released integration through HACS on a real Home
   Assistant instance.
7. Reload the config entry and verify one gateway poll plus one safe command on
   a real Salus gateway.
8. Check Home Assistant release notes for integration API deprecations affecting
   config entries, entity platforms, diagnostics, or manifest metadata.
