"""Tests for the Salus climate entity."""

from __future__ import annotations

import pytest
from homeassistant.components.climate import ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError
from salus_it600.const import (
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HoldType,
)
from salus_it600.device_models import (
    SQ610_HOLD_AUTO,
    SQ610_HOLD_AWAY,
    SQ610_HOLD_PERMANENT,
    SQ610_HOLD_STANDBY,
    SQ610_MODE_COOL,
    SQ610_RUNNING_COOL,
    SQ610_RUNNING_HEAT,
)
from salus_it600.exceptions import IT600ConnectionError

from custom_components.salus._climate_state import (
    PRESET_AWAY,
    PRESET_ECO,
    PRESET_FOLLOW_SCHEDULE,
    PRESET_PERMANENT_HOLD,
    PRESET_SCHEDULE_OVERRIDE,
    PRESET_STANDBY,
    RAW_PRESET_AWAY,
    RAW_PRESET_ECO,
    RAW_PRESET_FOLLOW_SCHEDULE,
    RAW_PRESET_OFF,
    RAW_PRESET_PERMANENT_HOLD,
    RAW_PRESET_SCHEDULE_OVERRIDE,
)
from custom_components.salus.climate import SalusThermostat
from custom_components.salus.const import DOMAIN
from custom_components.salus.coordinator import SalusData
from tests.conftest import FakeCoordinator, make_climate_device, make_fc600_device


def _normalized_sq610_device(device, fields):
    """Return a fake SQ610 device with normalized client fields applied."""
    if not fields:
        return device

    props = fields.get(device.unique_id, fields)
    if "hold_type" in props:
        device.hold_type = props["hold_type"]
        device.preset_mode = (
            RAW_PRESET_FOLLOW_SCHEDULE
            if device.hold_type == SQ610_HOLD_AUTO
            else RAW_PRESET_PERMANENT_HOLD
            if device.hold_type == SQ610_HOLD_PERMANENT
            else RAW_PRESET_AWAY
            if device.hold_type == SQ610_HOLD_AWAY
            else RAW_PRESET_SCHEDULE_OVERRIDE
            if device.hold_type == HoldType.TEMPORARY_HOLD
            else RAW_PRESET_OFF
            if device.hold_type == SQ610_HOLD_STANDBY
            else device.preset_mode
        )
        device.preset_modes = _sq610_raw_preset_modes(device.preset_mode)
    if "system_mode" in props:
        device.system_mode = props["system_mode"]
        device.hvac_mode = "cool" if device.system_mode == SQ610_MODE_COOL else "heat"
    if "running_state" in props:
        device.running_state = props["running_state"]
        device.hvac_action = (
            CURRENT_HVAC_COOL
            if device.running_state == SQ610_RUNNING_COOL
            else CURRENT_HVAC_HEAT
            if device.running_state == SQ610_RUNNING_HEAT
            else CURRENT_HVAC_IDLE
        )
    if "heating_setpoint" in props:
        device.heating_setpoint = props["heating_setpoint"]
    if "cooling_setpoint" in props:
        device.cooling_setpoint = props["cooling_setpoint"]
        device.supports_cooling = True
    if "current_humidity" in props:
        device.current_humidity = props["current_humidity"]
    if device.system_mode == SQ610_MODE_COOL:
        device.target_temperature = device.cooling_setpoint
    else:
        device.target_temperature = device.heating_setpoint
    return device


def _set_sq610_hold(device, hold_type: int) -> None:
    """Update a fake SQ610 device hold state."""
    device.hold_type = hold_type
    device.preset_mode = (
        RAW_PRESET_FOLLOW_SCHEDULE
        if hold_type == SQ610_HOLD_AUTO
        else RAW_PRESET_PERMANENT_HOLD
        if hold_type == SQ610_HOLD_PERMANENT
        else RAW_PRESET_AWAY
        if hold_type == SQ610_HOLD_AWAY
        else RAW_PRESET_SCHEDULE_OVERRIDE
        if hold_type == HoldType.TEMPORARY_HOLD
        else RAW_PRESET_OFF
        if hold_type == SQ610_HOLD_STANDBY
        else device.preset_mode
    )
    device.preset_modes = _sq610_raw_preset_modes(device.preset_mode)


def _sq610_raw_preset_modes(active_preset: str) -> list[str]:
    """Return the normalized client preset list for a fake SQ610."""
    modes = [
        RAW_PRESET_FOLLOW_SCHEDULE,
        RAW_PRESET_PERMANENT_HOLD,
        RAW_PRESET_AWAY,
        RAW_PRESET_OFF,
    ]
    if active_preset == RAW_PRESET_SCHEDULE_OVERRIDE:
        modes.insert(1, RAW_PRESET_SCHEDULE_OVERRIDE)
    return modes


def _coordinator_with_climate(device, normalized_fields=None):
    """Create a FakeCoordinator with one climate device."""
    device = _normalized_sq610_device(device, normalized_fields)
    data = SalusData(
        climate_devices={device.unique_id: device},
        binary_sensor_devices={},
        switch_devices={},
        cover_devices={},
        sensor_devices={},
    )
    return FakeCoordinator(data=data)


def _thermostat(device=None, normalized_fields=None):
    """Create a thermostat entity with its fake device and coordinator."""
    device = device or make_climate_device()
    coord = _coordinator_with_climate(device, normalized_fields)
    return device, coord, SalusThermostat(coord, device.unique_id)


def _gateway_call(method, device, *args):
    """Return one expected fake gateway call."""
    return (method, device.unique_id, *args)


def _fields(device, **values):
    """Return normalized field overrides for one fake device."""
    return {device.unique_id: values}


def _assert_gateway_calls(coord, *calls) -> None:
    """Assert exact fake gateway calls."""
    assert coord.gateway.calls == list(calls)


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
        fields = {device.unique_id: {"running_state": 1, "system_mode": 4}}
        coord = _coordinator_with_climate(device, fields)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.hvac_action == HVACAction.HEATING

    def test_hvac_action_idle(self):
        device = make_climate_device(hvac_action="idle")
        fields = {device.unique_id: {"running_state": 0, "system_mode": 4}}
        coord = _coordinator_with_climate(device, fields)
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

    def test_extra_state_attributes_includes_normalized_state(self):
        device = make_climate_device(
            hvac_mode="heat", preset_mode="Permanent Hold"
        )
        fields = {
            device.unique_id: {
                "system_mode": 4,
                "running_state": 1,
                "hold_type": 2,
            }
        }
        coord = _coordinator_with_climate(device, fields)
        entity = SalusThermostat(coord, device.unique_id)
        attrs = entity.extra_state_attributes
        assert attrs["salus_hvac_mode"] == "heat"
        assert attrs["salus_preset_mode"] == "Permanent Hold"
        assert attrs["salus_system_mode"] == 4
        assert attrs["salus_running_state"] == 1
        assert attrs["salus_hold_type"] == 2

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

    def test_preset_modes_for_sq610(self):
        """Test that SQ610 exposes all supported preset modes."""
        device = make_climate_device()
        coord = _coordinator_with_climate(device)
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.preset_modes == [
            PRESET_PERMANENT_HOLD,
            PRESET_FOLLOW_SCHEDULE,
            PRESET_AWAY,
        ]

    def test_preset_modes_for_sq610_follow_schedule_hides_override(self):
        """Schedule Override not exposed when SQ610 is in Follow Schedule."""
        device = make_climate_device()
        _, _, entity = _thermostat(
            device,
            _fields(device, hold_type=SQ610_HOLD_AUTO),
        )
        assert entity.preset_modes == [
            PRESET_PERMANENT_HOLD,
            PRESET_FOLLOW_SCHEDULE,
            PRESET_AWAY,
        ]

    def test_preset_modes_for_sq610_temporary_hold_shows_override(self):
        """Schedule Override exposed when SQ610 reports HoldType 1."""
        device = make_climate_device()
        _, _, entity = _thermostat(
            device,
            _fields(device, hold_type=HoldType.TEMPORARY_HOLD),
        )
        assert entity.preset_modes == [
            PRESET_PERMANENT_HOLD,
            PRESET_FOLLOW_SCHEDULE,
            PRESET_SCHEDULE_OVERRIDE,
            PRESET_AWAY,
        ]

    def test_preset_modes_for_sq610_away_hides_override(self):
        """Schedule Override not exposed when SQ610 is in Away."""
        device = make_climate_device()
        _, _, entity = _thermostat(
            device,
            _fields(device, hold_type=SQ610_HOLD_AWAY),
        )
        assert entity.preset_modes == [
            PRESET_PERMANENT_HOLD,
            PRESET_FOLLOW_SCHEDULE,
            PRESET_AWAY,
        ]

    async def test_schedule_override_rejected_when_not_exposed(self):
        """Selecting Schedule Override when in Follow Schedule is a no-op."""
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(device, hold_type=SQ610_HOLD_AUTO),
        )
        assert PRESET_SCHEDULE_OVERRIDE not in entity.preset_modes

        await entity.async_set_preset_mode(PRESET_SCHEDULE_OVERRIDE)

        _assert_gateway_calls(coord)  # no gateway calls


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
        entity = SalusThermostat(coord, device.unique_id)
        assert entity.preset_modes == [
            PRESET_PERMANENT_HOLD,
            PRESET_FOLLOW_SCHEDULE,
            PRESET_ECO,
        ]


# ---------------------------------------------------------------------------
# SQ610 Command tests
# ---------------------------------------------------------------------------


class TestSQ610Commands:
    """Test SQ610 thermostat command forwarding."""

    async def test_set_temperature(self):
        device, coord, entity = _thermostat()

        await entity.async_set_temperature(temperature=23.5)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_temperature", device, 23.5),
        )
        assert coord.refresh_requests == 1

    async def test_set_temperature_no_value_is_noop(self):
        _, coord, entity = _thermostat()

        await entity.async_set_temperature()

        assert coord.gateway.calls == []
        assert coord.refresh_requests == 0

    async def test_set_temperature_while_standby_is_noop(self):
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(
                device,
                hold_type=SQ610_HOLD_STANDBY,
                heating_setpoint=21.0,
            ),
        )

        await entity.async_set_temperature(temperature=23.5)

        assert coord.gateway.calls == []
        assert coord.refresh_requests == 0

    async def test_set_temperature_in_scheduled_cooling_uses_cooling_setpoint(self):
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(
                device,
                system_mode=SQ610_MODE_COOL,
                hold_type=SQ610_HOLD_AUTO,
                cooling_setpoint=22.5,
                heating_setpoint=21.0,
            ),
        )

        assert entity.hvac_mode == HVACMode.COOL
        assert entity.preset_mode == PRESET_FOLLOW_SCHEDULE

        await entity.async_set_temperature(temperature=23.5)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_temperature", device, 23.5),
        )
        assert coord.refresh_requests == 1

    @pytest.mark.parametrize(
        ("hvac_mode", "field_values", "expected_call"),
        [
            (
                HVACMode.HEAT,
                {},
                ("set_climate_mode", HVACMode.HEAT),
            ),
            (
                HVACMode.OFF,
                {"hold_type": SQ610_HOLD_PERMANENT},
                ("set_climate_preset", RAW_PRESET_OFF),
            ),
        ],
    )
    async def test_set_hvac_mode_simple_commands(
        self,
        hvac_mode,
        field_values,
        expected_call,
    ):
        device = make_climate_device()
        _, coord, entity = _thermostat(device, _fields(device, **field_values))

        await entity.async_set_hvac_mode(hvac_mode)

        method, *args = expected_call
        _assert_gateway_calls(coord, _gateway_call(method, device, *args))

    async def test_set_hvac_mode_auto_is_ignored_for_sq610(self):
        _, coord, entity = _thermostat()

        await entity.async_set_hvac_mode(HVACMode.AUTO)

        assert coord.gateway.calls == []

    async def test_set_hvac_mode_heat_from_standby_restores_permanent_hold(self):
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(device, hold_type=SQ610_HOLD_PERMANENT),
        )

        await entity.async_set_hvac_mode(HVACMode.OFF)
        _set_sq610_hold(device, SQ610_HOLD_STANDBY)
        await entity.async_set_hvac_mode(HVACMode.HEAT)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, RAW_PRESET_OFF),
            _gateway_call("set_climate_mode", device, HVACMode.HEAT),
            _gateway_call("set_climate_preset", device, RAW_PRESET_PERMANENT_HOLD),
        )

    async def test_set_hvac_mode_heat_from_standby_restores_follow_schedule(self):
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(
                device,
                system_mode=SQ610_MODE_COOL,
                hold_type=SQ610_HOLD_AUTO,
                cooling_setpoint=22.5,
            ),
        )

        await entity.async_set_hvac_mode(HVACMode.OFF)
        _set_sq610_hold(device, SQ610_HOLD_STANDBY)
        await entity.async_set_hvac_mode(HVACMode.HEAT)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, RAW_PRESET_OFF),
            _gateway_call("set_climate_mode", device, HVACMode.HEAT),
            _gateway_call("set_climate_preset", device, RAW_PRESET_FOLLOW_SCHEDULE),
        )

    async def test_set_hvac_mode_heat_from_standby_without_memory_defaults_to_hold(
        self,
    ):
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(device, hold_type=SQ610_HOLD_STANDBY),
        )

        await entity.async_set_hvac_mode(HVACMode.HEAT)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_mode", device, HVACMode.HEAT),
            _gateway_call("set_climate_preset", device, RAW_PRESET_PERMANENT_HOLD),
        )

    async def test_set_hvac_mode_while_scheduled_preserves_schedule(self):
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(
                device,
                system_mode=SQ610_MODE_COOL,
                hold_type=SQ610_HOLD_AUTO,
                cooling_setpoint=22.5,
            ),
        )

        await entity.async_set_hvac_mode(HVACMode.HEAT)

        _assert_gateway_calls(coord, _gateway_call("set_climate_mode", device, HVACMode.HEAT))

    @pytest.mark.parametrize(
        ("preset_mode", "raw_preset"),
        [
            (PRESET_FOLLOW_SCHEDULE, RAW_PRESET_FOLLOW_SCHEDULE),
            (PRESET_PERMANENT_HOLD, RAW_PRESET_PERMANENT_HOLD),
            (PRESET_AWAY, RAW_PRESET_AWAY),
            (PRESET_STANDBY, RAW_PRESET_OFF),
        ],
    )
    async def test_set_preset_modes(self, preset_mode, raw_preset):
        device, coord, entity = _thermostat()

        await entity.async_set_preset_mode(preset_mode)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, raw_preset),
        )

    async def test_schedule_override_is_report_only_when_active(self):
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(device, hold_type=HoldType.TEMPORARY_HOLD),
        )
        assert PRESET_SCHEDULE_OVERRIDE in entity.preset_modes

        await entity.async_set_preset_mode(PRESET_SCHEDULE_OVERRIDE)

        _assert_gateway_calls(coord)  # no gateway calls

    async def test_set_preset_while_standby_turns_on(self):
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(device, hold_type=SQ610_HOLD_STANDBY),
        )

        await entity.async_set_preset_mode(PRESET_FOLLOW_SCHEDULE)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, RAW_PRESET_FOLLOW_SCHEDULE),
        )

    async def test_physical_preset_change_updates_resume_memory(self):
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(device, hold_type=SQ610_HOLD_PERMANENT),
        )

        assert entity.preset_mode == PRESET_PERMANENT_HOLD

        _set_sq610_hold(device, SQ610_HOLD_AUTO)

        assert entity.preset_mode == PRESET_FOLLOW_SCHEDULE

        await entity.async_set_hvac_mode(HVACMode.OFF)
        _set_sq610_hold(device, SQ610_HOLD_STANDBY)
        await entity.async_set_hvac_mode(HVACMode.HEAT)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, RAW_PRESET_OFF),
            _gateway_call("set_climate_mode", device, HVACMode.HEAT),
            _gateway_call("set_climate_preset", device, RAW_PRESET_FOLLOW_SCHEDULE),
        )

    async def test_preset_mode_away(self):
        """Test that Away preset mode is recognized."""
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(device, hold_type=SQ610_HOLD_AWAY),
        )

        assert entity.preset_mode == PRESET_AWAY

    async def test_preset_mode_schedule_override(self):
        """Test that Schedule Override preset mode is recognized."""
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(device, hold_type=HoldType.TEMPORARY_HOLD),
        )

        assert entity.preset_mode == PRESET_SCHEDULE_OVERRIDE

    async def test_unknown_hold_type_does_not_overwrite_resume_memory(self):
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(device, hold_type=SQ610_HOLD_AUTO),
        )

        assert entity.preset_mode == PRESET_FOLLOW_SCHEDULE

        _set_sq610_hold(device, 99)

        assert entity.preset_mode == PRESET_FOLLOW_SCHEDULE

        await entity.async_set_hvac_mode(HVACMode.OFF)
        _set_sq610_hold(device, SQ610_HOLD_STANDBY)
        await entity.async_set_hvac_mode(HVACMode.HEAT)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, RAW_PRESET_OFF),
            _gateway_call("set_climate_mode", device, HVACMode.HEAT),
            _gateway_call("set_climate_preset", device, RAW_PRESET_FOLLOW_SCHEDULE),
        )

    async def test_sq610_cooling_support_stays_available_after_sparse_payload(self):
        device = make_climate_device()
        _, _, entity = _thermostat(
            device,
            _fields(
                device,
                system_mode=SQ610_MODE_COOL,
                hold_type=SQ610_HOLD_AUTO,
                cooling_setpoint=22.5,
            ),
        )

        assert entity.hvac_modes == [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]

        _set_sq610_hold(device, SQ610_HOLD_AUTO)
        device.hvac_modes = ["heat"]
        device.supports_cooling = False

        assert entity.hvac_modes == [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]

    @pytest.mark.parametrize(
        "fields",
        [
            {"system_mode": SQ610_MODE_COOL},
            {"running_state": SQ610_RUNNING_COOL},
        ],
    )
    async def test_sq610_runtime_cooling_state_proves_cooling_support(self, fields):
        device = make_climate_device(supports_cooling=False, hvac_modes=["heat"])
        _, _, entity = _thermostat(
            device,
            _fields(
                device,
                hold_type=SQ610_HOLD_PERMANENT,
                **fields,
            ),
        )

        assert entity.hvac_modes == [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]

    @pytest.mark.parametrize(
        ("method", "raw_preset"),
        [
            ("async_turn_off", RAW_PRESET_OFF),
            ("async_turn_on", RAW_PRESET_PERMANENT_HOLD),
        ],
    )
    async def test_turn_on_off_simple_commands(self, method, raw_preset):
        device, coord, entity = _thermostat()

        await getattr(entity, method)()

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, raw_preset),
        )

    async def test_turn_on_restores_remembered_schedule(self):
        device = make_climate_device()
        _, coord, entity = _thermostat(
            device,
            _fields(device, hold_type=SQ610_HOLD_AUTO),
        )

        await entity.async_set_hvac_mode(HVACMode.OFF)
        _set_sq610_hold(device, SQ610_HOLD_STANDBY)
        await entity.async_turn_on()

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, RAW_PRESET_OFF),
            _gateway_call("set_climate_preset", device, RAW_PRESET_FOLLOW_SCHEDULE),
        )

    async def test_commands_trigger_refresh(self):
        _, coord, entity = _thermostat()

        await entity.async_set_temperature(temperature=20.0)
        await entity.async_set_hvac_mode(HVACMode.HEAT)
        await entity.async_set_preset_mode(PRESET_FOLLOW_SCHEDULE)

        assert coord.refresh_requests == 3

    async def test_gateway_error_raises_home_assistant_error(self):
        _, coord, entity = _thermostat()
        coord.gateway.command_error = IT600ConnectionError("offline")

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
        device, coord, entity = _thermostat(make_fc600_device())

        await entity.async_set_fan_mode("high")

        _assert_gateway_calls(coord, _gateway_call("set_climate_fan_mode", device, "High"))

    async def test_set_temperature_non_sq610(self):
        device, coord, entity = _thermostat(make_fc600_device())

        await entity.async_set_temperature(temperature=24.0)

        _assert_gateway_calls(coord, _gateway_call("set_climate_temperature", device, 24.0))

    async def test_set_temperature_fc600_eco_is_noop(self):
        device = make_fc600_device()
        device.preset_mode = RAW_PRESET_ECO
        _, coord, entity = _thermostat(device)

        await entity.async_set_temperature(temperature=24.0)

        assert coord.gateway.calls == []
        assert coord.refresh_requests == 0

    @pytest.mark.parametrize(
        ("preset_mode", "raw_preset"),
        [
            (PRESET_FOLLOW_SCHEDULE, RAW_PRESET_FOLLOW_SCHEDULE),
            (PRESET_ECO, RAW_PRESET_ECO),
        ],
    )
    async def test_set_preset_modes(self, preset_mode, raw_preset):
        device, coord, entity = _thermostat(make_fc600_device())

        await entity.async_set_preset_mode(preset_mode)

        _assert_gateway_calls(coord, _gateway_call("set_climate_preset", device, raw_preset))
        assert coord.refresh_requests == 1

    async def test_set_hvac_mode_fc600_off_uses_preset(self):
        device = make_fc600_device()
        device.preset_mode = RAW_PRESET_FOLLOW_SCHEDULE
        _, coord, entity = _thermostat(device)

        await entity.async_set_hvac_mode(HVACMode.OFF)

        _assert_gateway_calls(coord, _gateway_call("set_climate_preset", device, RAW_PRESET_OFF))
        assert coord.refresh_requests == 1

    @pytest.mark.parametrize("model", ["FC600", "FC600NH"])
    async def test_set_hvac_mode_fc600_from_off_restores_eco(self, model):
        device = make_fc600_device()
        device.model = model
        device.hvac_mode = "cool"
        device.preset_mode = RAW_PRESET_ECO
        _, coord, entity = _thermostat(device)

        await entity.async_set_hvac_mode(HVACMode.OFF)
        device.preset_mode = RAW_PRESET_OFF
        await entity.async_set_hvac_mode(HVACMode.HEAT)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, RAW_PRESET_OFF),
            _gateway_call("set_climate_mode", device, HVACMode.HEAT),
            _gateway_call("set_climate_preset", device, RAW_PRESET_ECO),
        )

    async def test_set_preset_fc600_while_off_turns_on(self):
        device = make_fc600_device()
        device.preset_mode = RAW_PRESET_OFF
        _, coord, entity = _thermostat(device)

        await entity.async_set_preset_mode(PRESET_ECO)

        _assert_gateway_calls(coord, _gateway_call("set_climate_preset", device, RAW_PRESET_ECO))

    async def test_standard_heat_only_device_uses_single_hvac_menu(self):
        device = make_climate_device(
            model="HTRP-RF(50)",
            hvac_modes=["heat"],
            preset_mode="Follow Schedule",
        )
        _, coord, entity = _thermostat(device)

        assert entity.hvac_mode == HVACMode.AUTO
        assert entity.hvac_modes == [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
        assert entity.preset_modes == []
        assert not (entity.supported_features & ClimateEntityFeature.PRESET_MODE)

        await entity.async_set_hvac_mode(HVACMode.AUTO)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, RAW_PRESET_FOLLOW_SCHEDULE),
        )
        assert coord.refresh_requests == 1

    async def test_standard_heat_only_turn_on_sends_permanent_hold(self):
        device = make_climate_device(
            model="HTRP-RF(50)",
            hvac_modes=["heat"],
            preset_mode=RAW_PRESET_OFF,
        )
        _, coord, entity = _thermostat(device)

        assert entity.preset_modes == []

        await entity.async_turn_on()

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, RAW_PRESET_PERMANENT_HOLD),
        )
        assert coord.refresh_requests == 1

    @pytest.mark.parametrize(
        ("preset_mode", "hvac_mode", "raw_preset"),
        [
            ("Follow Schedule", HVACMode.HEAT, RAW_PRESET_PERMANENT_HOLD),
            ("Permanent Hold", HVACMode.OFF, RAW_PRESET_OFF),
        ],
    )
    async def test_standard_heat_only_mode_sets_preset(
        self,
        preset_mode,
        hvac_mode,
        raw_preset,
    ):
        device = make_climate_device(
            model="HTRP-RF(50)",
            hvac_modes=["heat"],
            preset_mode=preset_mode,
        )
        _, coord, entity = _thermostat(device)

        await entity.async_set_hvac_mode(hvac_mode)

        _assert_gateway_calls(
            coord,
            _gateway_call("set_climate_preset", device, raw_preset),
        )
        assert coord.refresh_requests == 1


# ---------------------------------------------------------------------------
# Capability gating tests
# ---------------------------------------------------------------------------


class TestPresetCapabilityGating:
    """Verify that family-specific presets are rejected for unsupported devices."""

    async def test_away_rejected_for_fc600(self):
        device = make_fc600_device()
        _, coord, entity = _thermostat(device)

        await entity.async_set_preset_mode(PRESET_AWAY)

        _assert_gateway_calls(coord)  # no gateway calls

    async def test_schedule_override_rejected_for_fc600_without_active_override(self):
        device = make_fc600_device()
        _, coord, entity = _thermostat(device)

        await entity.async_set_preset_mode(PRESET_SCHEDULE_OVERRIDE)

        _assert_gateway_calls(coord)  # no gateway calls

    async def test_schedule_override_report_only_for_fc600_when_active(self):
        device = make_fc600_device()
        device.hold_type = HoldType.TEMPORARY_HOLD
        device.preset_mode = RAW_PRESET_SCHEDULE_OVERRIDE
        _, coord, entity = _thermostat(device)

        assert entity.preset_modes == [
            PRESET_PERMANENT_HOLD,
            PRESET_FOLLOW_SCHEDULE,
            PRESET_SCHEDULE_OVERRIDE,
            PRESET_ECO,
        ]

        await entity.async_set_preset_mode(PRESET_SCHEDULE_OVERRIDE)

        _assert_gateway_calls(coord)  # no gateway calls

    @pytest.mark.parametrize("preset_mode", [PRESET_AWAY, PRESET_SCHEDULE_OVERRIDE])
    async def test_sq610_specific_presets_rejected_for_heat_only(self, preset_mode):
        device = make_climate_device(
            model="HTRP-RF(50)",
            hvac_modes=["heat"],
            preset_mode="Follow Schedule",
        )
        _, coord, entity = _thermostat(device)

        await entity.async_set_preset_mode(preset_mode)

        _assert_gateway_calls(coord)  # no gateway calls

    async def test_eco_rejected_for_sq610(self):
        device, coord, entity = _thermostat()

        await entity.async_set_preset_mode(PRESET_ECO)

        _assert_gateway_calls(coord)  # no gateway calls
