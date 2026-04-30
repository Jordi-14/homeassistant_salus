"""Tests for the Salus switch entity."""

from __future__ import annotations

import pytest
from homeassistant.exceptions import HomeAssistantError
from salus_it600.exceptions import IT600ConnectionError

from custom_components.salus.const import DOMAIN
from custom_components.salus.coordinator import SalusData
from custom_components.salus.switch import SalusSwitch
from tests.conftest import FakeCoordinator, make_switch_device


def _coordinator_with_switches(*devices):
    """Create a FakeCoordinator with switch devices."""
    data = SalusData(
        climate_devices={},
        binary_sensor_devices={},
        switch_devices={d.unique_id: d for d in devices},
        cover_devices={},
        sensor_devices={},
        raw_climate_props={},
    )
    return FakeCoordinator(data=data)


class TestSalusSwitchProperties:
    """Test switch entity property delegation."""

    def test_unique_id(self):
        device = make_switch_device(unique_id="switch_001_1")
        coord = _coordinator_with_switches(device)
        entity = SalusSwitch(coord, "switch_001_1")
        assert entity.unique_id == "switch_001_1"

    def test_is_on_true(self):
        device = make_switch_device(is_on=True)
        coord = _coordinator_with_switches(device)
        entity = SalusSwitch(coord, device.unique_id)
        assert entity.is_on is True

    def test_is_on_false(self):
        device = make_switch_device(is_on=False)
        coord = _coordinator_with_switches(device)
        entity = SalusSwitch(coord, device.unique_id)
        assert entity.is_on is False

    def test_device_class_outlet(self):
        device = make_switch_device(device_class="outlet")
        coord = _coordinator_with_switches(device)
        entity = SalusSwitch(coord, device.unique_id)
        assert entity.device_class == "outlet"

    def test_device_info(self):
        device = make_switch_device(unique_id="switch_001", model="SP600")
        coord = _coordinator_with_switches(device)
        entity = SalusSwitch(coord, "switch_001")
        info = entity.device_info
        assert info["manufacturer"] == "SALUS"
        assert info["model"] == "SP600"
        assert (DOMAIN, "switch_001") in info["identifiers"]

    def test_available_true(self):
        device = make_switch_device(available=True)
        coord = _coordinator_with_switches(device)
        entity = SalusSwitch(coord, device.unique_id)
        assert entity.available is True

    def test_available_false(self):
        device = make_switch_device(available=False)
        coord = _coordinator_with_switches(device)
        entity = SalusSwitch(coord, device.unique_id)
        assert entity.available is False


class TestSalusSwitchCommands:
    """Test switch command forwarding."""

    async def test_turn_on(self):
        device = make_switch_device(unique_id="switch_001_1")
        coord = _coordinator_with_switches(device)
        entity = SalusSwitch(coord, device.unique_id)
        await entity.async_turn_on()
        assert ("turn_on_switch", "switch_001_1") in coord.gateway.calls

    async def test_turn_off(self):
        device = make_switch_device(unique_id="switch_001_1")
        coord = _coordinator_with_switches(device)
        entity = SalusSwitch(coord, device.unique_id)
        await entity.async_turn_off()
        assert ("turn_off_switch", "switch_001_1") in coord.gateway.calls

    async def test_turn_on_triggers_refresh(self):
        device = make_switch_device()
        coord = _coordinator_with_switches(device)
        entity = SalusSwitch(coord, device.unique_id)
        await entity.async_turn_on()
        assert coord.refresh_requests == 1

    async def test_turn_off_triggers_refresh(self):
        device = make_switch_device()
        coord = _coordinator_with_switches(device)
        entity = SalusSwitch(coord, device.unique_id)
        await entity.async_turn_off()
        assert coord.refresh_requests == 1

    async def test_gateway_error_raises(self):
        device = make_switch_device()
        coord = _coordinator_with_switches(device)
        coord.gateway.command_error = IT600ConnectionError("timeout")
        entity = SalusSwitch(coord, device.unique_id)
        with pytest.raises(HomeAssistantError, match="Failed to"):
            await entity.async_turn_on()
