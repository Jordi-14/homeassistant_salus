"""Tests for the Salus cover entity."""

from __future__ import annotations

import pytest
from homeassistant.components.cover import CoverEntityFeature
from homeassistant.exceptions import HomeAssistantError
from salus_it600.exceptions import IT600ConnectionError

from custom_components.salus.const import DOMAIN
from custom_components.salus.coordinator import SalusData
from custom_components.salus.cover import SalusCover
from tests.conftest import FakeCoordinator, make_cover_device


def _coordinator_with_covers(*devices):
    """Create a FakeCoordinator with cover devices."""
    data = SalusData(
        climate_devices={},
        binary_sensor_devices={},
        switch_devices={},
        cover_devices={d.unique_id: d for d in devices},
        sensor_devices={},
        raw_climate_props={},
    )
    return FakeCoordinator(data=data)


class TestSalusCoverProperties:
    """Test cover entity property delegation."""

    def test_unique_id(self):
        device = make_cover_device(unique_id="cover_001")
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, "cover_001")
        assert entity.unique_id == "cover_001"

    def test_current_cover_position(self):
        device = make_cover_device(current_cover_position=75)
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        assert entity.current_cover_position == 75

    def test_is_closed_false(self):
        device = make_cover_device(is_closed=False, current_cover_position=75)
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        assert entity.is_closed is False

    def test_is_closed_true(self):
        device = make_cover_device(is_closed=True, current_cover_position=0)
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        assert entity.is_closed is True
        assert entity.current_cover_position == 0

    def test_is_opening_none(self):
        device = make_cover_device(is_opening=None)
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        assert entity.is_opening is None

    def test_is_closing_none(self):
        device = make_cover_device(is_closing=None)
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        assert entity.is_closing is None

    def test_supported_features(self):
        device = make_cover_device(supported_features=7)  # OPEN|CLOSE|SET_POSITION
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        features = entity.supported_features
        assert features & CoverEntityFeature.OPEN
        assert features & CoverEntityFeature.CLOSE
        assert features & CoverEntityFeature.SET_POSITION

    def test_device_class_shutter_from_model(self):
        """RS600/SR600 models get 'shutter' device class."""
        device = make_cover_device(model="RS600", device_class=None)
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        assert entity.device_class == "shutter"

    def test_device_info(self):
        device = make_cover_device(unique_id="cover_001", model="RS600")
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, "cover_001")
        info = entity.device_info
        assert info["manufacturer"] == "SALUS"
        assert info["model"] == "RS600"
        assert (DOMAIN, "cover_001") in info["identifiers"]

    def test_available_true(self):
        device = make_cover_device(available=True)
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        assert entity.available is True

    def test_available_false(self):
        device = make_cover_device(available=False)
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        assert entity.available is False


class TestSalusCoverCommands:
    """Test cover command forwarding."""

    async def test_open_cover(self):
        device = make_cover_device(unique_id="cover_001")
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        await entity.async_open_cover()
        assert ("open_cover", "cover_001") in coord.gateway.calls

    async def test_close_cover(self):
        device = make_cover_device(unique_id="cover_001")
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        await entity.async_close_cover()
        assert ("close_cover", "cover_001") in coord.gateway.calls

    async def test_set_cover_position(self):
        device = make_cover_device(unique_id="cover_001")
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        await entity.async_set_cover_position(position=50)
        assert ("set_cover_position", "cover_001", 50) in coord.gateway.calls

    async def test_set_cover_position_none_is_noop(self):
        device = make_cover_device()
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        await entity.async_set_cover_position()
        assert coord.gateway.calls == []
        assert coord.refresh_requests == 0

    async def test_commands_trigger_refresh(self):
        device = make_cover_device()
        coord = _coordinator_with_covers(device)
        entity = SalusCover(coord, device.unique_id)
        await entity.async_open_cover()
        await entity.async_close_cover()
        await entity.async_set_cover_position(position=25)
        assert coord.refresh_requests == 3

    async def test_gateway_error_raises(self):
        device = make_cover_device()
        coord = _coordinator_with_covers(device)
        coord.gateway.command_error = IT600ConnectionError("offline")
        entity = SalusCover(coord, device.unique_id)
        with pytest.raises(HomeAssistantError, match="Failed to"):
            await entity.async_open_cover()
