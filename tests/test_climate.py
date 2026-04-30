"""Tests for the Salus climate entity."""

from __future__ import annotations

import pytest
from homeassistant.components.climate import ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.exceptions import HomeAssistantError
from salus_it600.exceptions import IT600ConnectionError

from custom_components.salus._climate_state import (
    PRESET_FOLLOW_SCHEDULE,
    PRESET_PERMANENT_HOLD,
    PRESET_STANDBY,
    RAW_PRESET_FOLLOW_SCHEDULE,
    RAW_PRESET_OFF,
    RAW_PRESET_PERMANENT_HOLD,
)
from custom_components.salus.climate import SalusThermostat
from custom_components.salus.const import DOMAIN
from custom_components.salus.coordinator import SalusData
from tests.conftest import FakeCoordinator, make_climate_device, make_fc600_device


def _coordinator_with_climate(device, raw_props=None):
    """Create a FakeCoordinator with one climate device."""
    data = SalusData(
        climate_devices={device.unique_id: device},
        binary_sensor_devices={},
        switch_devices={},
        cover_devices={},
        sensor_devices={},
        raw_climate_props=raw_props or {},
    )
    return FakeCoordinator(data=data)


# ---------------------------------------------------------------------------
# Property tests (iT600 / SQ610)
# ---------------------------------------------------------------------------


class TestSQ610Properties:
    """Test SQ610 thermostat entity properties."""

    def test_unique_id(self):
        device = make_climate_device(unique_id="climate_001")
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, "climate_001")
        assert entity.unique_id == "climate_001"

    def test_current_temperature(self):
        device = make_climate_device(current_temperature=21.5)
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.current_temperature == 21.5

    def test_target_temperature(self):
        device = make_climate_device(target_temperature=22.0)
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.target_temperature == 22.0

    def test_min_max_temp(self):
        device = make_climate_device(min_temp=5.0, max_temp=35.0)
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.min_temp == 5.0
        assert entity.max_temp == 35.0

    def test_precision(self):
        device = make_climate_device(precision=0.1)
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.precision == 0.1

    def test_hvac_action(self):
        device = make_climate_device(hvac_action="heating")
        raw_props = {device.unique_id: {"RunningState": 1, "SystemMode": 4}}
        coord = _coordinator_with_climate(device, raw_props)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.hvac_action == HVACAction.HEATING

    def test_hvac_action_idle(self):
        device = make_climate_device(hvac_action="idle")
        raw_props = {device.unique_id: {"RunningState": 0, "SystemMode": 4}}
        coord = _coordinator_with_climate(device, raw_props)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.hvac_action == HVACAction.IDLE

    def test_current_humidity(self):
        device = make_climate_device(current_humidity=45.0)
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.current_humidity == 45.0

    def test_current_humidity_none(self):
        device = make_climate_device(current_humidity=None)
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.current_humidity is None

    def test_temperature_unit(self):
        from homeassistant.const import UnitOfTemperature

        device = make_climate_device(temperature_unit="°C")
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.temperature_unit == UnitOfTemperature.CELSIUS

    def test_supported_features_no_fan(self):
        device = make_climate_device(fan_mode=None, fan_modes=None)
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        features = entity.supported_features
        assert features & ClimateEntityFeature.TARGET_TEMPERATURE
        assert features & ClimateEntityFeature.PRESET_MODE
        assert not (features & ClimateEntityFeature.FAN_MODE)

    def test_fan_mode_none_for_sq610(self):
        device = make_climate_device(fan_mode=None, fan_modes=None)
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.fan_mode is None
        assert entity.fan_modes is None

    def test_locked_property(self):
        device = make_climate_device(locked=True)
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.locked is True

    def test_extra_state_attributes_includes_raw_state(self):
        device = make_climate_device(
            hvac_mode="heat", preset_mode="Permanent Hold"
        )
        raw_props = {
            device.unique_id: {
                "SystemMode": 4,
                "RunningState": 1,
                "HoldType": 2,
            }
        }
        coord = _coordinator_with_climate(device, raw_props)
        entity = SalusThermostat(coord, device.unique_id)
        attrs = entity.extra_state_attributes
        assert attrs["salus_raw_hvac_mode"] == "heat"
        assert attrs["salus_raw_preset_mode"] == "Permanent Hold"
        assert attrs["salus_raw_system_mode"] == 4
        assert attrs["salus_raw_running_state"] == 1
        assert attrs["salus_raw_hold_type"] == 2

    def test_extra_state_attributes_with_valve_opening(self):
        device = make_climate_device(
            model="TRV3RF",
            extra_state_attributes={"valve_opening": 42},
        )
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        attrs = entity.extra_state_attributes
        assert attrs["valve_opening"] == 42

    def test_device_info(self):
        device = make_climate_device(unique_id="climate_001", model="SQ610RF")
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, "climate_001")
        info = entity.device_info
        assert info["manufacturer"] == "SALUS"
        assert info["model"] == "SQ610RF"
        assert (DOMAIN, "climate_001") in info["identifiers"]
        assert info["via_device"] == (DOMAIN, "gateway-1")

    def test_available_true(self):
        device = make_climate_device(available=True)
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.available is True

    def test_available_false_when_device_offline(self):
        device = make_climate_device(available=False)
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.available is False

    def test_available_false_when_device_missing(self):
        coord = FakeCoordinator()  # empty data
        entity = SalusThermostat(coord, "nonexistent")
        assert entity.available is False


# ---------------------------------------------------------------------------
# FC600 fan-coil tests
# ---------------------------------------------------------------------------


class TestFC600Properties:
    """Test FC600 fan-coil thermostat specifics."""

    def test_supported_features_with_fan(self):
        device = make_fc600_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        features = entity.supported_features
        assert features & ClimateEntityFeature.FAN_MODE

    def test_fan_mode(self):
        device = make_fc600_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.fan_mode == "auto"

    def test_fan_modes_list(self):
        device = make_fc600_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert "auto" in entity.fan_modes
        assert "high" in entity.fan_modes
        assert "low" in entity.fan_modes

    def test_preset_modes_include_eco(self):
        device = make_fc600_device()
        coord = _coordinator_with_climate(device)
        SalusThermostat(coord, device.unique_id)
        # FC600 exposes its own preset list from the library
        assert "Follow Schedule" in device.preset_modes


# ---------------------------------------------------------------------------
# SQ610 Command tests
# ---------------------------------------------------------------------------


class TestSQ610Commands:
    """Test SQ610 thermostat command forwarding."""

    async def test_set_temperature(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_temperature(temperature=23.5)
        assert coord.gateway.calls == [
            ("set_sq610_temperature", device.unique_id, 23.5, False)
        ]
        assert coord.refresh_requests == 1

    async def test_set_temperature_no_value_is_noop(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_temperature()
        assert coord.gateway.calls == []
        assert coord.refresh_requests == 0

    async def test_set_hvac_mode_heat(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_hvac_mode(HVACMode.HEAT)
        assert coord.gateway.calls == [
            ("set_sq610_hvac_mode", device.unique_id, HVACMode.HEAT)
        ]

    async def test_set_hvac_mode_off_uses_preset(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_hvac_mode(HVACMode.OFF)
        assert coord.gateway.calls == [
            ("set_sq610_preset", device.unique_id, RAW_PRESET_OFF)
        ]

    async def test_set_hvac_mode_auto_uses_follow_schedule(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_hvac_mode(HVACMode.AUTO)
        assert coord.gateway.calls == [
            ("set_sq610_preset", device.unique_id, RAW_PRESET_FOLLOW_SCHEDULE)
        ]

    async def test_set_preset_follow_schedule(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_preset_mode(PRESET_FOLLOW_SCHEDULE)
        assert coord.gateway.calls == [
            ("set_sq610_preset", device.unique_id, RAW_PRESET_FOLLOW_SCHEDULE)
        ]

    async def test_set_preset_permanent_hold(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_preset_mode(PRESET_PERMANENT_HOLD)
        assert coord.gateway.calls == [
            ("set_sq610_preset", device.unique_id, RAW_PRESET_PERMANENT_HOLD)
        ]

    async def test_set_preset_standby(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_preset_mode(PRESET_STANDBY)
        assert coord.gateway.calls == [
            ("set_sq610_preset", device.unique_id, RAW_PRESET_OFF)
        ]

    async def test_turn_off(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_turn_off()
        assert coord.gateway.calls == [
            ("set_sq610_preset", device.unique_id, RAW_PRESET_OFF)
        ]

    async def test_turn_on(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_turn_on()
        assert coord.gateway.calls == [
            ("set_sq610_preset", device.unique_id, RAW_PRESET_PERMANENT_HOLD)
        ]

    async def test_commands_trigger_refresh(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_temperature(temperature=20.0)
        await entity.async_set_hvac_mode(HVACMode.HEAT)
        await entity.async_set_preset_mode(PRESET_FOLLOW_SCHEDULE)
        assert coord.refresh_requests == 3

    async def test_gateway_error_raises_home_assistant_error(self):
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        coord.gateway.command_error = IT600ConnectionError("offline")
        entity = SalusThermostat(coord, device.unique_id)
        with pytest.raises(HomeAssistantError, match="Failed to"):
            await entity.async_set_preset_mode(PRESET_FOLLOW_SCHEDULE)
        assert coord.gateway.calls == []
        assert coord.refresh_requests == 0


# ---------------------------------------------------------------------------
# FC600 Command tests
# ---------------------------------------------------------------------------


class TestFC600Commands:
    """Test FC600 fan-coil command forwarding."""

    async def test_set_fan_mode(self):
        device = make_fc600_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_fan_mode("high")
        assert ("set_climate_fan_mode", device.unique_id, "High") in coord.gateway.calls

    async def test_set_temperature_non_sq610(self):
        device = make_fc600_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_temperature(temperature=24.0)
        assert ("set_climate_temperature", device.unique_id, 24.0) in coord.gateway.calls

    async def test_set_preset_non_sq610(self):
        device = make_fc600_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        await entity.async_set_preset_mode(PRESET_FOLLOW_SCHEDULE)
        assert (
            "set_climate_preset",
            device.unique_id,
            RAW_PRESET_FOLLOW_SCHEDULE,
        ) in coord.gateway.calls
