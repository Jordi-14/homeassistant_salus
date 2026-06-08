"""Climate state interpretation tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
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
    HoldType,
)
from salus_it600.const import (
    PRESET_ECO as RAW_PRESET_ECO,
)
from salus_it600.const import (
    PRESET_FOLLOW_SCHEDULE as RAW_PRESET_FOLLOW_SCHEDULE,
)
from salus_it600.device_models import (
    SQ610_HOLD_AUTO,
    SQ610_HOLD_PERMANENT,
    SQ610_HOLD_STANDBY,
    SQ610_MODE_COOL,
    SQ610_MODE_HEAT,
    SQ610_RUNNING_COOL,
    SQ610_RUNNING_HEAT,
)

from custom_components.salus._climate_state import (
    PRESET_AWAY,
    PRESET_ECO,
    PRESET_FOLLOW_SCHEDULE,
    PRESET_PERMANENT_HOLD,
    PRESET_SCHEDULE_OVERRIDE,
    RAW_PRESET_AWAY,
    RAW_PRESET_SCHEDULE_OVERRIDE,
    build_climate_view_state,
)

TURN_ON_OFF_FEATURES = (
    getattr(ClimateEntityFeature, "TURN_ON", ClimateEntityFeature(0))
    | getattr(ClimateEntityFeature, "TURN_OFF", ClimateEntityFeature(0))
)


def _device(**overrides: Any) -> SimpleNamespace:
    values = {
        "model": "HTRP-RF(50)",
        "hvac_mode": HVAC_MODE_HEAT,
        "hvac_action": "idle",
        "hvac_modes": [HVAC_MODE_HEAT],
        "preset_mode": RAW_PRESET_FOLLOW_SCHEDULE,
        "preset_modes": [
            RAW_PRESET_FOLLOW_SCHEDULE,
            "Permanent Hold",
            PRESET_OFF,
        ],
        "current_temperature": 20.0,
        "current_humidity": None,
        "target_temperature": 21.0,
        "fan_mode": None,
        "fan_modes": None,
        "hold_type": None,
        "system_mode": None,
        "running_state": None,
        "heating_setpoint": None,
        "cooling_setpoint": None,
        "supports_cooling": False,
    }
    values.update(overrides)
    if "preset_modes" not in overrides:
        if values["model"] == "SQ610RF":
            values["preset_modes"] = [
                RAW_PRESET_FOLLOW_SCHEDULE,
                "Permanent Hold",
                RAW_PRESET_AWAY,
                PRESET_OFF,
            ]
            if "preset_mode" not in overrides:
                values["preset_mode"] = _raw_sq610_preset_mode(values["hold_type"])
            if values["preset_mode"] == RAW_PRESET_SCHEDULE_OVERRIDE:
                values["preset_modes"].insert(1, RAW_PRESET_SCHEDULE_OVERRIDE)
        elif values["model"] in {"FC600", "FC600NH"}:
            values["preset_modes"] = [
                RAW_PRESET_FOLLOW_SCHEDULE,
                "Permanent Hold",
                RAW_PRESET_ECO,
                PRESET_OFF,
            ]
            if "preset_mode" not in overrides:
                values["preset_mode"] = _raw_fc600_preset_mode(values["hold_type"])
            if values["preset_mode"] == RAW_PRESET_SCHEDULE_OVERRIDE:
                values["preset_modes"].insert(1, RAW_PRESET_SCHEDULE_OVERRIDE)
    return SimpleNamespace(**values)


def _raw_sq610_preset_mode(hold_type: Any) -> str:
    if hold_type == SQ610_HOLD_STANDBY:
        return PRESET_OFF
    if hold_type == HoldType.AWAY:
        return RAW_PRESET_AWAY
    if hold_type == HoldType.TEMPORARY_HOLD:
        return RAW_PRESET_SCHEDULE_OVERRIDE
    if hold_type == SQ610_HOLD_PERMANENT:
        return "Permanent Hold"
    return RAW_PRESET_FOLLOW_SCHEDULE


def _raw_fc600_preset_mode(hold_type: Any) -> str:
    if hold_type == SQ610_HOLD_STANDBY:
        return PRESET_OFF
    if hold_type == HoldType.ECO:
        return RAW_PRESET_ECO
    if hold_type == HoldType.TEMPORARY_HOLD:
        return RAW_PRESET_SCHEDULE_OVERRIDE
    if hold_type == SQ610_HOLD_PERMANENT:
        return "Permanent Hold"
    return RAW_PRESET_FOLLOW_SCHEDULE


def _state(device_overrides: dict[str, Any] | None = None, **state_kwargs: Any):
    return build_climate_view_state(_device(**(device_overrides or {})), **state_kwargs)


def _attrs(state, *attrs: str) -> tuple[Any, ...]:
    return tuple(getattr(state, attr) for attr in attrs)


SQ610_COOLING = {
    "model": "SQ610RF",
    "system_mode": SQ610_MODE_COOL,
    "running_state": SQ610_RUNNING_COOL,
    "cooling_setpoint": 22.5,
    "heating_setpoint": 21.0,
    "target_temperature": 22.5,
    "supports_cooling": True,
}


@pytest.mark.parametrize(
    ("device_overrides", "state_kwargs", "attrs", "expected"),
    [
        pytest.param(
            {**SQ610_COOLING, "hold_type": SQ610_HOLD_PERMANENT},
            {},
            (
                "supports_cooling",
                "hvac_modes",
                "hvac_mode",
                "hvac_action",
                "target_temperature",
                "preset_mode",
                "preset_modes",
            ),
            (
                True,
                [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL],
                HVACMode.COOL,
                HVACAction.COOLING,
                22.5,
                PRESET_PERMANENT_HOLD,
                [PRESET_PERMANENT_HOLD, PRESET_FOLLOW_SCHEDULE, PRESET_AWAY],
            ),
            id="sq610_cooling_setpoint",
        ),
        pytest.param(
            {**SQ610_COOLING, "hold_type": SQ610_HOLD_AUTO},
            {},
            ("hvac_mode", "target_temperature", "preset_mode"),
            (HVACMode.COOL, 22.5, PRESET_FOLLOW_SCHEDULE),
            id="sq610_auto_cooling",
        ),
        pytest.param(
            {
                **SQ610_COOLING,
                "system_mode": SQ610_MODE_HEAT,
                "running_state": SQ610_RUNNING_HEAT,
                "target_temperature": 21.0,
                "hold_type": SQ610_HOLD_AUTO,
            },
            {},
            ("hvac_mode", "target_temperature", "preset_mode"),
            (HVACMode.HEAT, 21.0, PRESET_FOLLOW_SCHEDULE),
            id="sq610_auto_heating",
        ),
        pytest.param(
            {
                "model": "SQ610RF",
                "current_temperature": 22.35,
                "hold_type": SQ610_HOLD_PERMANENT,
                "heating_setpoint": 21.0,
            },
            {},
            ("current_temperature",),
            (22.35,),
            id="sq610_current_temperature",
        ),
        pytest.param(
            {
                "model": "SQ610RF",
                "current_humidity": 63.0,
                "hold_type": SQ610_HOLD_PERMANENT,
                "heating_setpoint": 21.0,
            },
            {},
            ("current_humidity",),
            (63.0,),
            id="sq610_humidity_percent",
        ),
        pytest.param(
            {
                "model": "SQ610RF",
                "current_humidity": 45.5,
                "hold_type": SQ610_HOLD_PERMANENT,
                "heating_setpoint": 21.0,
            },
            {},
            ("current_humidity",),
            (45.5,),
            id="sq610_humidity_fractional",
        ),
        pytest.param(
            {
                "model": "SQ610RF",
                "running_state": SQ610_RUNNING_HEAT,
                "hold_type": SQ610_HOLD_STANDBY,
                "heating_setpoint": 21.0,
            },
            {},
            ("hvac_mode", "hvac_action", "preset_mode"),
            (HVACMode.OFF, HVACAction.OFF, None),
            id="sq610_standby",
        ),
        pytest.param(
            {
                "model": "SQ610RF",
                "running_state": SQ610_RUNNING_HEAT,
                "hold_type": SQ610_HOLD_STANDBY,
                "heating_setpoint": 21.0,
            },
            {"sq610_resume_preset_mode": PRESET_FOLLOW_SCHEDULE},
            ("hvac_mode", "preset_mode"),
            (HVACMode.OFF, None),
            id="sq610_standby_hides_resume",
        ),
        pytest.param(
            {"model": "SQ610RF", "hold_type": 99, "heating_setpoint": 21.0},
            {"sq610_resume_preset_mode": PRESET_FOLLOW_SCHEDULE},
            ("preset_mode",),
            (PRESET_FOLLOW_SCHEDULE,),
            id="sq610_unknown_hold_uses_resume",
        ),
        pytest.param(
            {
                "model": "SQ610RF",
                "hold_type": SQ610_HOLD_AUTO,
                "heating_setpoint": 21.0,
            },
            {},
            ("hvac_mode", "preset_mode"),
            (HVACMode.HEAT, PRESET_FOLLOW_SCHEDULE),
            id="sq610_auto_without_system_state",
        ),
        pytest.param(
            {
                "model": "SQ610RF",
                "hold_type": SQ610_HOLD_PERMANENT,
                "heating_setpoint": 21.0,
                "supports_cooling": False,
            },
            {},
            ("hvac_modes", "supports_cooling"),
            ([HVACMode.OFF, HVACMode.HEAT], False),
            id="sq610_heat_only",
        ),
        pytest.param(
            {
                "model": "SQ610RF",
                "hold_type": SQ610_HOLD_PERMANENT,
                "heating_setpoint": 21.0,
                "supports_cooling": False,
            },
            {"sq610_known_supports_cooling": True},
            ("supports_cooling", "hvac_modes"),
            (True, [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]),
            id="sq610_remembers_cooling_support",
        ),
    ],
)
def test_sq610_view_state_cases(device_overrides, state_kwargs, attrs, expected) -> None:
    assert _attrs(_state(device_overrides, **state_kwargs), *attrs) == expected


@pytest.mark.parametrize(
    ("device_overrides", "attrs", "expected"),
    [
        pytest.param(
            {"preset_mode": PRESET_OFF},
            ("hvac_mode", "hvac_action", "hvac_modes", "preset_mode", "preset_modes"),
            (
                HVACMode.OFF,
                HVACAction.OFF,
                [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO],
                None,
                [],
            ),
            id="standard_off",
        ),
        pytest.param(
            {},
            ("hvac_mode", "hvac_modes", "preset_mode", "preset_modes"),
            (HVACMode.AUTO, [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO], None, []),
            id="standard_heat_only",
        ),
    ],
)
def test_standard_view_state_cases(device_overrides, attrs, expected) -> None:
    state = _state(device_overrides)
    assert _attrs(state, *attrs) == expected
    if not device_overrides:
        assert state.supported_features == (
            ClimateEntityFeature.TARGET_TEMPERATURE | TURN_ON_OFF_FEATURES
        )


@pytest.mark.parametrize("model", ["FC600", "FC600NH"])
def test_fc600_fan_modes_are_exposed(model: str) -> None:
    state = _state(
        {
            "model": model,
            "hvac_mode": HVACMode.COOL,
            "hvac_action": CURRENT_HVAC_COOL,
            "preset_modes": [
                RAW_PRESET_FOLLOW_SCHEDULE,
                "Permanent Hold",
                RAW_PRESET_ECO,
                PRESET_OFF,
            ],
            "fan_mode": FAN_MODE_HIGH,
            "fan_modes": [FAN_MODE_AUTO, FAN_MODE_HIGH],
        }
    )

    assert _attrs(
        state,
        "supports_cooling",
        "hvac_modes",
        "hvac_mode",
        "preset_modes",
        "fan_modes",
    ) == (
        True,
        [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL],
        HVACMode.COOL,
        [PRESET_PERMANENT_HOLD, PRESET_FOLLOW_SCHEDULE, PRESET_ECO],
        ["auto", "high"],
    )
    assert state.supported_features & ClimateEntityFeature.FAN_MODE
    if model == "FC600":
        assert state.fan_mode == "high"


@pytest.mark.parametrize(
    ("device_overrides", "state_kwargs", "attrs", "expected"),
    [
        pytest.param(
            {
                "model": "FC600",
                "hvac_mode": HVACMode.COOL,
                "preset_mode": PRESET_OFF,
                "fan_mode": FAN_MODE_AUTO,
                "fan_modes": [FAN_MODE_AUTO, FAN_MODE_HIGH],
            },
            {},
            ("hvac_mode", "hvac_action", "preset_mode"),
            (HVACMode.OFF, HVACAction.OFF, None),
            id="fc600_off",
        ),
        pytest.param(
            {
                "model": "FC600",
                "hvac_mode": HVACMode.COOL,
                "preset_mode": PRESET_OFF,
                "fan_mode": FAN_MODE_AUTO,
                "fan_modes": [FAN_MODE_AUTO, FAN_MODE_HIGH],
            },
            {"fc600_resume_preset_mode": PRESET_ECO},
            ("hvac_mode", "preset_mode"),
            (HVACMode.OFF, None),
            id="fc600_off_hides_resume",
        ),
        pytest.param(
            {
                "model": "FC600",
                "hvac_mode": HVACMode.HEAT,
                "preset_mode": RAW_PRESET_ECO,
                "fan_mode": FAN_MODE_AUTO,
                "fan_modes": [FAN_MODE_AUTO, FAN_MODE_HIGH],
            },
            {},
            ("hvac_mode", "preset_mode"),
            (HVACMode.HEAT, PRESET_ECO),
            id="fc600_eco",
        ),
    ],
)
def test_fc600_view_state_cases(device_overrides, state_kwargs, attrs, expected) -> None:
    assert _attrs(_state(device_overrides, **state_kwargs), *attrs) == expected


def test_fc600_reported_schedule_override_is_in_preset_modes_without_hold_type() -> None:
    """Keep the active FC600 preset available when HoldType is unavailable."""
    state = _state(
        {
            "model": "FC600",
            "preset_mode": RAW_PRESET_SCHEDULE_OVERRIDE,
            "hold_type": None,
        }
    )

    assert state.preset_mode == PRESET_SCHEDULE_OVERRIDE
    assert state.preset_modes == [
        PRESET_PERMANENT_HOLD,
        PRESET_FOLLOW_SCHEDULE,
        PRESET_SCHEDULE_OVERRIDE,
        PRESET_ECO,
    ]
