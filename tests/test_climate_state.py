"""Climate state interpretation tests."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from tests.ha_shim import ClimateEntityFeature, HVACAction, HVACMode, install

install()

from custom_components.salus._climate_state import (  # noqa: E402
    PRESET_FOLLOW_SALUS_SCHEDULE,
    PRESET_STANDBY,
    RAW_PRESET_PERMANENT_HOLD,
    build_climate_view_state,
)
from salus_it600.const import (  # noqa: E402
    CURRENT_HVAC_COOL,
    FAN_MODE_AUTO,
    FAN_MODE_HIGH,
    HVAC_MODE_HEAT,
    PRESET_FOLLOW_SCHEDULE,
    PRESET_OFF,
)
from salus_it600.device_models import (  # noqa: E402
    SQ610_HOLD_AUTO,
    SQ610_HOLD_PERMANENT,
    SQ610_HOLD_STANDBY,
    SQ610_MODE_COOL,
    SQ610_RUNNING_COOL,
    SQ610_RUNNING_HEAT,
)


def _device(**overrides: Any) -> SimpleNamespace:
    values = {
        "model": "HTRP-RF(50)",
        "hvac_mode": HVAC_MODE_HEAT,
        "hvac_action": "idle",
        "hvac_modes": [HVAC_MODE_HEAT],
        "preset_mode": PRESET_FOLLOW_SCHEDULE,
        "current_temperature": 20.0,
        "current_humidity": None,
        "target_temperature": 21.0,
        "fan_mode": None,
        "fan_modes": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class TestClimateViewState(unittest.TestCase):
    def test_sq610_cooling_uses_raw_cooling_setpoint(self) -> None:
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

        self.assertTrue(state.supports_cooling)
        self.assertEqual(HVACMode.COOL, state.hvac_mode)
        self.assertEqual(HVACAction.COOLING, state.hvac_action)
        self.assertEqual(22.5, state.target_temperature)
        self.assertEqual(RAW_PRESET_PERMANENT_HOLD, state.preset_mode)

    def test_sq610_current_temperature_uses_raw_temperature_measurement(self) -> None:
        state = build_climate_view_state(
            _device(model="SQ610RF", current_temperature=20.0),
            {
                "HoldType": SQ610_HOLD_PERMANENT,
                "MeasuredValue_x100": 2235,
                "HeatingSetpoint_x100": 2100,
            },
        )

        self.assertEqual(22.35, state.current_temperature)

    def test_sq610_humidity_uses_raw_percent_value(self) -> None:
        state = build_climate_view_state(
            _device(model="SQ610RF", current_humidity=0.63),
            {
                "HoldType": SQ610_HOLD_PERMANENT,
                "SunnySetpoint_x100": 63,
                "HeatingSetpoint_x100": 2100,
            },
        )

        self.assertEqual(63.0, state.current_humidity)

    def test_sq610_humidity_accepts_x100_value(self) -> None:
        state = build_climate_view_state(
            _device(model="SQ610RF"),
            {
                "HoldType": SQ610_HOLD_PERMANENT,
                "SunnySetpoint_x100": 4550,
                "HeatingSetpoint_x100": 2100,
            },
        )

        self.assertEqual(45.5, state.current_humidity)

    def test_sq610_standby_maps_to_off_action_and_standby_preset(self) -> None:
        state = build_climate_view_state(
            _device(model="SQ610RF"),
            {
                "RunningState": SQ610_RUNNING_HEAT,
                "HoldType": SQ610_HOLD_STANDBY,
                "HeatingSetpoint_x100": 2100,
            },
        )

        self.assertEqual(HVACAction.OFF, state.hvac_action)
        self.assertEqual(PRESET_STANDBY, state.preset_mode)

    def test_sq610_auto_hold_maps_to_follow_salus_schedule(self) -> None:
        state = build_climate_view_state(
            _device(model="SQ610RF"),
            {"HoldType": SQ610_HOLD_AUTO, "HeatingSetpoint_x100": 2100},
        )

        self.assertEqual(PRESET_FOLLOW_SALUS_SCHEDULE, state.preset_mode)

    def test_standard_off_preset_maps_to_standby(self) -> None:
        state = build_climate_view_state(
            _device(preset_mode=PRESET_OFF),
            {},
        )

        self.assertEqual(PRESET_STANDBY, state.preset_mode)
        self.assertEqual([HVACMode.HEAT], state.hvac_modes)

    def test_fc600_fan_modes_are_exposed(self) -> None:
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

        self.assertTrue(state.supports_cooling)
        self.assertEqual(HVACMode.COOL, state.hvac_mode)
        self.assertEqual("high", state.fan_mode)
        self.assertEqual(["auto", "high"], state.fan_modes)
        self.assertTrue(state.supported_features & ClimateEntityFeature.FAN_MODE)


if __name__ == "__main__":
    unittest.main()
