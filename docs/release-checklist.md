# Release Checklist

1. Run the `salus-it600-client` test suite and coverage report.
2. Publish the intended `salus-it600-client` version to PyPI.
3. Update `custom_components/salus/manifest.json` to pin that exact client version.
4. Run the Home Assistant integration compile and test checks.
5. Tag and release `homeassistant_salus`.
