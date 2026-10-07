"""Register Salus devices through the installed Home Assistant registry API."""

from __future__ import annotations

import pytest
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.salus.entity as entity_module
from custom_components.salus.climate import SalusThermostat
from custom_components.salus.const import DOMAIN
from custom_components.salus.coordinator import SalusData
from custom_components.salus.lock import SalusThermostatLock
from tests.conftest import FakeCoordinator, make_climate_device


def _coordinator():
    device = make_climate_device(unique_id="thermostat-1", model="SQ610RFNH")
    return FakeCoordinator(
        data=SalusData(
            climate_devices={device.unique_id: device},
            binary_sensor_devices={},
            switch_devices={},
            cover_devices={},
            sensor_devices={},
        )
    )


async def test_climate_and_lock_register_with_the_installed_registry(hass):
    """Both platforms must register on legacy and modern Home Assistant."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    registry = dr.async_get(hass)
    coordinator = _coordinator()
    gateway = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, coordinator.gateway_id)},
    )
    coordinator.gateway_device_id = gateway.id

    for entity_type in (SalusThermostat, SalusThermostatLock):
        entity = entity_type(coordinator, "thermostat-1")
        registered = registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            **entity.device_info,
        )
        assert registered.via_device_id == gateway.id


@pytest.mark.parametrize("modern_api", [False, True])
def test_gateway_link_uses_only_the_supported_field(monkeypatch, modern_api):
    monkeypatch.setattr(entity_module, "_SUPPORTS_VIA_DEVICE_ID", modern_api)
    coordinator = _coordinator()
    for entity_type in (SalusThermostat, SalusThermostatLock):
        info = entity_type(coordinator, "thermostat-1").device_info
        if modern_api:
            assert info["via_device_id"] == "gateway-device-1"
            assert "via_device" not in info
        else:
            assert info["via_device"] == (DOMAIN, "gateway-1")
            assert "via_device_id" not in info


def test_gateway_device_does_not_link_to_itself():
    coordinator = _coordinator()
    coordinator.gateway_id = "thermostat-1"
    info = SalusThermostat(coordinator, "thermostat-1").device_info
    assert "via_device" not in info
    assert "via_device_id" not in info
