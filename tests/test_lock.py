"""Tests for the Salus thermostat child-lock entity."""

from __future__ import annotations

import pytest
from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError
from salus_it600.exceptions import IT600ConnectionError

from custom_components.salus.const import DOMAIN
from custom_components.salus.coordinator import SalusData
from custom_components.salus.lock import SalusThermostatLock
from tests.conftest import FakeCoordinator, make_climate_device


def _coordinator_with_lockable_climate(device):
    """Create a FakeCoordinator with a lockable climate device."""
    data = SalusData(
        climate_devices={device.unique_id: device},
        binary_sensor_devices={},
        switch_devices={},
        cover_devices={},
        sensor_devices={},
        raw_climate_props={},
    )
    return FakeCoordinator(data=data)


class TestSalusThermostatLockProperties:
    """Test lock entity property delegation."""

    def test_unique_id_has_lock_suffix(self):
        device = make_climate_device(unique_id="climate_001", locked=False)
        coord = _coordinator_with_lockable_climate(device)
        entity = SalusThermostatLock(coord, "climate_001")
        assert entity.unique_id == "climate_001_lock"

    def test_entity_category_config(self):
        device = make_climate_device(locked=False)
        coord = _coordinator_with_lockable_climate(device)
        entity = SalusThermostatLock(coord, device.unique_id)
        assert entity.entity_category == EntityCategory.CONFIG

    def test_is_locked_false(self):
        device = make_climate_device(locked=False)
        coord = _coordinator_with_lockable_climate(device)
        entity = SalusThermostatLock(coord, device.unique_id)
        assert entity.is_locked is False

    def test_is_locked_true(self):
        device = make_climate_device(locked=True)
        coord = _coordinator_with_lockable_climate(device)
        entity = SalusThermostatLock(coord, device.unique_id)
        assert entity.is_locked is True

    def test_device_info_links_to_thermostat(self):
        device = make_climate_device(unique_id="climate_001", locked=False)
        coord = _coordinator_with_lockable_climate(device)
        entity = SalusThermostatLock(coord, "climate_001")
        info = entity.device_info
        assert (DOMAIN, "climate_001") in info["identifiers"]


class TestSalusThermostatLockCommands:
    """Test lock/unlock forwarding to the gateway."""

    async def test_async_lock(self):
        device = make_climate_device(unique_id="climate_001", locked=False)
        coord = _coordinator_with_lockable_climate(device)
        entity = SalusThermostatLock(coord, "climate_001")
        await entity.async_lock()
        assert ("set_climate_locked", "climate_001", True) in coord.gateway.calls
        assert coord.refresh_requests == 1

    async def test_async_unlock(self):
        device = make_climate_device(unique_id="climate_001", locked=True)
        coord = _coordinator_with_lockable_climate(device)
        entity = SalusThermostatLock(coord, "climate_001")
        await entity.async_unlock()
        assert ("set_climate_locked", "climate_001", False) in coord.gateway.calls
        assert coord.refresh_requests == 1

    async def test_gateway_error_raises(self):
        device = make_climate_device(locked=False)
        coord = _coordinator_with_lockable_climate(device)
        coord.gateway.command_error = IT600ConnectionError("offline")
        entity = SalusThermostatLock(coord, device.unique_id)
        with pytest.raises(HomeAssistantError, match="Failed to"):
            await entity.async_lock()
