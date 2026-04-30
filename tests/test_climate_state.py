"""Climate state interpretation tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from salus_it600.const import (
    CURRENT_HVAC_COOL,
    FAN_MODE_AUTO,
    FAN_MODE_HIGH,
    HVAC_MODE_HEAT,
    PRESET_OFF,
)
from salus_it600.const import (
    PRESET_FOLLOW_SCHEDULE as RAW_PRESET_FOLLOW_SCHEDULE,
)
from salus_it600.device_models import (
    SQ610_HOLD_AUTO,
    SQ610_HOLD_PERMANENT,
    SQ610_HOLD_STANDBY,
    SQ610_MODE_COOL,
    SQ610_RUNNING_COOL,
    SQ610_RUNNING_HEAT,
)

from custom_components.salus._climate_state import (
    PRESET_FOLLOW_SCHEDULE,
    PRESET_PERMANENT_HOLD,
    PRESET_STANDBY,
    build_climate_view_state,
)


def _device(**overrides: Any) -> SimpleNamespace:
    values = {
        "model": "HTRP-RF(50)",
        "hvac_mode": HVAC_MODE_HEAT,
        "hvac_action": "idle",
        "hvac_modes": [HVAC_MODE_HEAT],
        "preset_mode": RAW_PRESET_FOLLOW_SCHEDULE,
        "current_temperature": 20.0,
        "current_humidity": None,
        "target_temperature": 21.0,
        "fan_mode": None,
        "fan_modes": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_sq610_cooling_uses_raw_cooling_setpoint() -> None:
    state = build_climate_view_state(
        _device(model="SQ610RF"),
        {
            "SystemMode": SQ610_MODE_COOL,
            "RunningState": SQ610_RUNNING_COOL,
            "HoldType": SQ610_HOLD_PERMANENT,
            "CoolingSetpoint_x100": 2250,
            "HeatingSetpoint_x100": 2100,
        },
    )

    assert state.supports_cooling is True
    assert state.hvac_mode == HVACMode.COOL
    assert state.hvac_action == HVACAction.COOLING
    assert state.target_temperature == 22.5
    assert state.preset_mode == PRESET_PERMANENT_HOLD


def test_sq610_current_temperature_uses_raw_temperature_measurement() -> None:
    state = build_climate_view_state(
        _device(model="SQ610RF", current_temperature=20.0),
        {
            "HoldType": SQ610_HOLD_PERMANENT,
            "MeasuredValue_x100": 2235,
            "HeatingSetpoint_x100": 2100,
        },
    )

    assert state.current_temperature == 22.35


def test_sq610_humidity_uses_raw_percent_value() -> None:
    state = build_climate_view_state(
        _device(model="SQ610RF", current_humidity=0.63),
        {
            "HoldType": SQ610_HOLD_PERMANENT,
            "SunnySetpoint_x100": 63,
            "HeatingSetpoint_x100": 2100,
        },
    )

    assert state.current_humidity == 63.0


def test_sq610_humidity_accepts_x100_value() -> None:
    state = build_climate_view_state(
        _device(model="SQ610RF"),
        {
            "HoldType": SQ610_HOLD_PERMANENT,
            "SunnySetpoint_x100": 4550,
            "HeatingSetpoint_x100": 2100,
        },
    )

    assert state.current_humidity == 45.5


def test_sq610_standby_maps_to_off_mode_and_off_action() -> None:
    state = build_climate_view_state(
        _device(model="SQ610RF"),
        {
            "RunningState": SQ610_RUNNING_HEAT,
            "HoldType": SQ610_HOLD_STANDBY,
            "HeatingSetpoint_x100": 2100,
        },
    )

    assert state.hvac_mode == HVACMode.OFF
    assert state.hvac_action == HVACAction.OFF
    assert state.preset_mode == PRESET_STANDBY


def test_sq610_auto_hold_maps_to_auto_mode_and_follow_schedule() -> None:
    state = build_climate_view_state(
        _device(model="SQ610RF"),
        {"HoldType": SQ610_HOLD_AUTO, "HeatingSetpoint_x100": 2100},
    )

    assert state.hvac_mode == HVACMode.AUTO
    assert state.preset_mode == PRESET_FOLLOW_SCHEDULE


def test_sq610_heat_only_exposes_off_heat_auto_modes() -> None:
    state = build_climate_view_state(
        _device(model="SQ610RF"),
        {"HoldType": SQ610_HOLD_PERMANENT, "HeatingSetpoint_x100": 2100},
    )

    assert state.hvac_modes == [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
    assert state.supports_cooling is False


def test_standard_off_preset_maps_to_standby() -> None:
    state = build_climate_view_state(
        _device(preset_mode=PRESET_OFF),
        {},
    )

    assert state.preset_mode == PRESET_STANDBY
    assert state.hvac_modes == [HVACMode.HEAT]


def test_supported_features_include_modern_turn_on_off_flags() -> None:
    state = build_climate_view_state(_device(), {})

    expected = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | getattr(ClimateEntityFeature, "TURN_ON", ClimateEntityFeature(0))
        | getattr(ClimateEntityFeature, "TURN_OFF", ClimateEntityFeature(0))
    )
    assert state.supported_features == expected


def test_fc600_fan_modes_are_exposed() -> None:
    state = build_climate_view_state(
        _device(
            model="FC600",
            hvac_mode=HVACMode.COOL,
            hvac_action=CURRENT_HVAC_COOL,
            fan_mode=FAN_MODE_HIGH,
            fan_modes=[FAN_MODE_AUTO, FAN_MODE_HIGH],
        ),
        {},
    )

    assert state.supports_cooling is True
    assert state.hvac_mode == HVACMode.COOL
    assert state.fan_mode == "high"
    assert state.fan_modes == ["auto", "high"]
    assert state.supported_features & ClimateEntityFeature.FAN_MODE
