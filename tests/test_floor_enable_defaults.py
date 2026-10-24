"""Only enable eligible floor selects previously disabled by the integration."""

from types import SimpleNamespace

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.salus import _async_enable_floor_comfort_entities
from custom_components.salus.const import DOMAIN


async def test_enable_floor_defaults_preserves_user_and_unrelated_entries(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    other = MockConfigEntry(domain=DOMAIN, unique_id="other")
    other.add_to_hass(hass)
    registry = er.async_get(hass)

    def create(domain, uid, disabled, config=entry):
        return registry.async_get_or_create(
            domain, DOMAIN, uid, config_entry=config, disabled_by=disabled
        )

    automatic = create(
        "select", "auto_comfort_warm_floor", er.RegistryEntryDisabler.INTEGRATION
    )
    manual = create(
        "select", "manual_comfort_warm_floor", er.RegistryEntryDisabler.USER
    )
    unsupported = create(
        "select", "unsupported_comfort_warm_floor", er.RegistryEntryDisabler.INTEGRATION
    )
    diagnostic = create("sensor", "auto_battery", er.RegistryEntryDisabler.INTEGRATION)
    other_gateway = create(
        "select",
        "other_comfort_warm_floor",
        er.RegistryEntryDisabler.INTEGRATION,
        other,
    )
    data = SimpleNamespace(
        climate_devices={
            key: SimpleNamespace(supports_comfort_warm_floor=True)
            for key in ("auto", "manual", "other")
        }
    )
    _async_enable_floor_comfort_entities(hass, entry, data)
    assert registry.async_get(automatic.entity_id).disabled_by is None
    for before in (manual, unsupported, diagnostic, other_gateway):
        assert registry.async_get(before.entity_id).disabled_by == before.disabled_by
    # Repeating setup is idempotent and never changes a user disable.
    _async_enable_floor_comfort_entities(hass, entry, data)
    assert (
        registry.async_get(manual.entity_id).disabled_by
        is er.RegistryEntryDisabler.USER
    )
