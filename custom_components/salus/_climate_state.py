"""Climate state interpretation for Salus thermostat entities."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_OFF,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from salus_it600.const import TEMPERATURE_SCALE
from salus_it600.device_models import (
    MODEL_FC600,
    SQ610_HOLD_AUTO,
    SQ610_HOLD_PERMANENT,
    SQ610_HOLD_STANDBY,
    SQ610_MODE_COOL,
    SQ610_MODE_EMERGENCY_HEAT,
    SQ610_MODE_HEAT,
    SQ610_RUNNING_COOL,
    SQ610_RUNNING_HEAT,
    is_sq610_model,
)

_LOGGER = logging.getLogger(__name__)

RAW_PRESET_FOLLOW_SCHEDULE = "Follow Schedule"
RAW_PRESET_PERMANENT_HOLD = "Permanent Hold"
RAW_PRESET_TEMPORARY_HOLD = "Temporary Hold"
RAW_PRESET_ECO = "Eco"
RAW_PRESET_OFF = "Off"

PRESET_PERMANENT_HOLD = "permanent_hold"
PRESET_STANDBY = "standby"
PRESET_FOLLOW_SCHEDULE = "follow_schedule"
EXPOSED_PRESET_MODES = [
    PRESET_PERMANENT_HOLD,
    PRESET_STANDBY,
    PRESET_FOLLOW_SCHEDULE,
]

RAW_TO_HA_FAN_MODE = {
    "Off": FAN_OFF,
    "Auto": FAN_AUTO,
    "Low": FAN_LOW,
    "Medium": FAN_MEDIUM,
    "High": FAN_HIGH,
}
HA_TO_RAW_FAN_MODE = {value: key for key, value in RAW_TO_HA_FAN_MODE.items()}

COOLING_ACTIONS = {"cooling", "cooling (idling)"}
MANUAL_PRESET_MODES = {
    RAW_PRESET_PERMANENT_HOLD,
    RAW_PRESET_TEMPORARY_HOLD,
    RAW_PRESET_ECO,
}
TURN_ON_OFF_FEATURES = (
    getattr(ClimateEntityFeature, "TURN_ON", ClimateEntityFeature(0))
    | getattr(ClimateEntityFeature, "TURN_OFF", ClimateEntityFeature(0))
)


@dataclass(frozen=True, slots=True)
class ClimateViewState:
    """Home Assistant-facing view of one Salus climate device snapshot."""

    supports_cooling: bool
    supported_features: ClimateEntityFeature
    current_temperature: float | None
    current_humidity: float | None
    hvac_mode: HVACMode
    hvac_modes: list[HVACMode]
    hvac_action: HVACAction | None
    target_temperature: float | None
    preset_mode: str | None
    preset_modes: list[str]
    fan_mode: str | None
    fan_modes: list[str] | None


def is_sq610_device(device: Any) -> bool:
    """Return whether the device is a Quantum thermostat."""
    return is_sq610_model(getattr(device, "model", None))


def build_climate_view_state(
    device: Any | None,
    raw_props: Mapping[str, Any],
) -> ClimateViewState:
    """Build the Home Assistant-facing state for a Salus climate device."""
    supports_cooling = _supports_cooling(device, raw_props)
    hvac_mode = _effective_hvac_mode(device, raw_props, supports_cooling)
    return ClimateViewState(
        supports_cooling=supports_cooling,
        supported_features=_supported_features(device),
        current_temperature=_current_temperature(device, raw_props),
        current_humidity=_current_humidity(device, raw_props),
        hvac_mode=hvac_mode,
        hvac_modes=_build_hvac_modes(device, supports_cooling),
        hvac_action=_hvac_action(device, raw_props),
        target_temperature=_target_temperature(device, raw_props, hvac_mode),
        preset_mode=_effective_preset_mode(device, raw_props),
        preset_modes=EXPOSED_PRESET_MODES,
        fan_mode=_fan_mode(device),
        fan_modes=_fan_modes(device),
    )


def _numeric_value(value: Any) -> float | None:
    """Return a numeric payload value, rejecting bools and non-numeric values."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _temperature_from_x100(*values: Any) -> float | None:
    """Return the first available x100 temperature value in Celsius."""
    for value in values:
        numeric_value = _numeric_value(value)
        if numeric_value is not None:
            return numeric_value / TEMPERATURE_SCALE
    return None


def _humidity_percent(raw_humidity: Any) -> float | None:
    """Return SQ610 humidity as a percent, accepting raw percent and x100 forms."""
    humidity = _numeric_value(raw_humidity)
    if humidity is None:
        return None

    if humidity > 100:
        humidity /= TEMPERATURE_SCALE

    if 0 <= humidity <= 100:
        return humidity

    _LOGGER.warning("Ignoring implausible SQ610 humidity value: %s", raw_humidity)
    return None


def _current_temperature(
    device: Any | None,
    raw_props: Mapping[str, Any],
) -> float | None:
    """Return the best current-temperature value for a thermostat."""
    if device is None:
        return None

    if is_sq610_device(device):
        raw_temperature = _temperature_from_x100(
            raw_props.get("LocalTemperature_x100"),
            raw_props.get("MeasuredValue_x100"),
        )
        if raw_temperature is not None:
            return raw_temperature

    return getattr(device, "current_temperature", None)


def _current_humidity(
    device: Any | None,
    raw_props: Mapping[str, Any],
) -> float | None:
    """Return the best current-humidity value for a thermostat."""
    if device is None:
        return None

    if is_sq610_device(device):
        raw_humidity = _humidity_percent(raw_props.get("SunnySetpoint_x100"))
        if raw_humidity is not None:
            return raw_humidity

    return getattr(device, "current_humidity", None)


def _normalize_hvac_action(action: Any) -> HVACAction | None:
    """Map library-specific strings to Home Assistant HVACAction values."""
    if isinstance(action, HVACAction):
        return action
    if action == "off":
        return HVACAction.OFF
    if action == "heating":
        return HVACAction.HEATING
    if action == "cooling":
        return HVACAction.COOLING
    if action in {"idle", "heating (idling)", "cooling (idling)"}:
        return HVACAction.IDLE
    if action is not None:
        _LOGGER.warning("Unknown Salus HVAC action: %s", action)
    return None


def _supports_cooling(device: Any | None, raw_props: Mapping[str, Any]) -> bool:
    """Return whether the thermostat exposes a separate cooling mode."""
    if not device:
        return False
    if is_sq610_device(device):
        # SQ610RF is heat-only; only report cooling if gateway confirms it
        return (
            raw_props.get("SystemMode") == SQ610_MODE_COOL
            or raw_props.get("RunningState") == SQ610_RUNNING_COOL
            or raw_props.get("CoolingSetpoint_x100") is not None
        )
    return bool(
        device.model == MODEL_FC600
        or HVACMode.COOL in (device.hvac_modes or [])
        or device.fan_modes is not None
        or raw_props.get("CoolingSetpoint_x100") is not None
    )


def _build_hvac_modes(device: Any | None, supports_cooling: bool) -> list[HVACMode]:
    """Return the HVAC modes to expose for a thermostat."""
    if device and is_sq610_device(device):
        modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
        if supports_cooling:
            modes.insert(2, HVACMode.COOL)
        return modes
    if supports_cooling:
        return [HVACMode.HEAT, HVACMode.COOL]
    return [HVACMode.HEAT]


def _effective_hvac_mode(
    device: Any | None,
    raw_props: Mapping[str, Any],
    supports_cooling: bool,
) -> HVACMode:
    """Return the Salus system mode we want to expose in Home Assistant."""
    if device is None:
        return HVACMode.HEAT

    if is_sq610_device(device):
        hold_type = raw_props.get("HoldType")
        system_mode = raw_props.get("SystemMode")
        running_state = raw_props.get("RunningState")
        if hold_type == SQ610_HOLD_STANDBY:
            return HVACMode.OFF
        if system_mode == SQ610_MODE_COOL or running_state == SQ610_RUNNING_COOL:
            return HVACMode.COOL
        if (
            system_mode in {SQ610_MODE_HEAT, SQ610_MODE_EMERGENCY_HEAT}
            or running_state == SQ610_RUNNING_HEAT
        ):
            return HVACMode.HEAT
        if hold_type == SQ610_HOLD_AUTO:
            return HVACMode.AUTO
        return HVACMode.HEAT

    if device.hvac_mode == HVACMode.COOL:
        return HVACMode.COOL
    if device.hvac_mode == HVACMode.HEAT:
        return HVACMode.HEAT
    if supports_cooling and device.hvac_action in COOLING_ACTIONS:
        return HVACMode.COOL
    return HVACMode.HEAT


def _effective_preset_mode(
    device: Any | None,
    raw_props: Mapping[str, Any],
) -> str | None:
    """Collapse Salus hold states into the smaller HA control surface."""
    if device is None:
        return None

    if is_sq610_device(device):
        hold_type = raw_props.get("HoldType")
        if hold_type == SQ610_HOLD_STANDBY:
            return PRESET_STANDBY
        if hold_type == SQ610_HOLD_PERMANENT:
            return PRESET_PERMANENT_HOLD
        if hold_type == SQ610_HOLD_AUTO:
            return PRESET_FOLLOW_SCHEDULE

    if device.preset_mode == RAW_PRESET_OFF:
        return PRESET_STANDBY
    if device.preset_mode in MANUAL_PRESET_MODES:
        return PRESET_PERMANENT_HOLD
    if device.preset_mode == RAW_PRESET_FOLLOW_SCHEDULE:
        return PRESET_FOLLOW_SCHEDULE
    return device.preset_mode


def _supported_features(device: Any | None) -> ClimateEntityFeature:
    """Return the climate features supported by the exposed HA entity."""
    if device is None:
        return ClimateEntityFeature(0)

    supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | TURN_ON_OFF_FEATURES
    )
    if not is_sq610_device(device) and device.fan_modes is not None:
        supported_features |= ClimateEntityFeature.FAN_MODE
    return supported_features


def _hvac_action(
    device: Any | None,
    raw_props: Mapping[str, Any],
) -> HVACAction | None:
    """Return the current HVAC action if supported."""
    if device is None:
        return None

    if is_sq610_device(device):
        hold_type = raw_props.get("HoldType")
        running_state = raw_props.get("RunningState")
        system_mode = raw_props.get("SystemMode")
        if hold_type == SQ610_HOLD_STANDBY:
            return HVACAction.OFF
        if running_state == SQ610_RUNNING_HEAT:
            return HVACAction.HEATING
        if running_state == SQ610_RUNNING_COOL:
            return HVACAction.COOLING
        if system_mode in {
            SQ610_MODE_COOL,
            SQ610_MODE_HEAT,
            SQ610_MODE_EMERGENCY_HEAT,
        }:
            return HVACAction.IDLE
        return None

    return _normalize_hvac_action(device.hvac_action)


def _target_temperature(
    device: Any | None,
    raw_props: Mapping[str, Any],
    hvac_mode: HVACMode,
) -> float | None:
    """Return the temperature the thermostat tries to reach."""
    if device is None:
        return None

    if is_sq610_device(device):
        raw_value = (
            raw_props.get("CoolingSetpoint_x100")
            if hvac_mode == HVACMode.COOL
            else raw_props.get("HeatingSetpoint_x100")
        )
        if raw_value is not None:
            return raw_value / 100
    return device.target_temperature


def _fan_mode(device: Any | None) -> str | None:
    """Return the active HA fan mode."""
    if device is None or is_sq610_device(device):
        return None
    return RAW_TO_HA_FAN_MODE.get(device.fan_mode)


def _fan_modes(device: Any | None) -> list[str] | None:
    """Return supported HA fan modes."""
    if device is None or is_sq610_device(device) or device.fan_modes is None:
        return None
    return [
        RAW_TO_HA_FAN_MODE[fan_mode]
        for fan_mode in device.fan_modes
        if fan_mode in RAW_TO_HA_FAN_MODE
    ]
