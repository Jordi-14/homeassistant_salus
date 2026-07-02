"""Diagnostics support for the Salus iT600 integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant

from .coordinator import SalusConfigEntry, SalusData, SalusRuntimeData

TO_REDACT = {CONF_HOST, CONF_TOKEN}

CLIMATE_SUPPORT_FIELDS = (
    "UniID",
    "DeviceName",
    "ModelIdentifier_i",
    "OnlineStatus_i",
    "FirmwareVersion",
    "LocalTemperature_x100",
    "MeasuredValue_x100",
    "HeatingControl",
    "CoolingControl",
    "HeatingSetpoint_x100",
    "CoolingSetpoint_x100",
    "MinHeatSetpoint_x100",
    "MaxHeatSetpoint_x100",
    "MinCoolSetpoint_x100",
    "MaxCoolSetpoint_x100",
    "SunnySetpoint_x100",
    "SystemMode",
    "RunningState",
    "HoldType",
    "LockKey",
    "LockKey_a",
)
CLIMATE_NORMALIZED_FIELDS = (
    "current_temperature",
    "current_humidity",
    "target_temperature",
    "min_temp",
    "max_temp",
    "hvac_mode",
    "hvac_action",
    "preset_mode",
    "fan_mode",
    "online_status",
    "hold_type",
    "system_mode",
    "running_state",
    "heating_setpoint",
    "cooling_setpoint",
    "min_heat_temp",
    "max_heat_temp",
    "min_cool_temp",
    "max_cool_temp",
    "heating_control",
    "cooling_control",
    "supports_cooling",
    "supports_fan",
    "supports_heat",
    "cooling_capability_source",
)
CLIMATE_NORMALIZED_SEQUENCE_FIELDS = (
    "hvac_modes",
    "preset_modes",
)
CLIMATE_NORMALIZED_OPTIONAL_SEQUENCE_FIELDS = ("fan_modes",)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: SalusConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a Salus config entry."""
    runtime_data = _runtime_data(entry)

    diagnostics: dict[str, Any] = {
        "entry": {
            "entry_id": getattr(entry, "entry_id", None),
            "title": getattr(entry, "title", None),
            "data": async_redact_data(dict(getattr(entry, "data", {})), TO_REDACT),
        },
    }

    if runtime_data is None:
        diagnostics["runtime"] = {"loaded": False}
        return diagnostics

    coordinator = runtime_data.coordinator
    data: SalusData | None = coordinator.data

    diagnostics.update(
        {
            "runtime": {"loaded": True},
            "gateway": async_redact_data(
                {
                    "id": coordinator.gateway_id,
                    "host": getattr(entry, "data", {}).get(CONF_HOST),
                    "health": coordinator.gateway_diagnostics(),
                },
                TO_REDACT,
            ),
            "device_counts": _device_counts(data),
            "device_availability": coordinator.device_availability_diagnostics(),
            "climate": _climate_diagnostics(data),
        }
    )
    return diagnostics


def _runtime_data(
    entry: SalusConfigEntry,
) -> SalusRuntimeData | None:
    """Return runtime data stored on the config entry."""
    return getattr(entry, "runtime_data", None)


def _device_counts(data: SalusData | None) -> dict[str, int]:
    """Return device counts by platform."""
    if data is None:
        return {}

    return {
        "climate": len(data.climate_devices),
        "binary_sensor": len(data.binary_sensor_devices),
        "switch": len(data.switch_devices),
        "cover": len(data.cover_devices),
        "sensor": len(data.sensor_devices),
    }


def _climate_diagnostics(data: SalusData | None) -> dict[str, Any]:
    """Return normalized climate diagnostics useful for field support."""
    if data is None:
        return {"devices": {}}

    devices: dict[str, Any] = {}
    for device_id, device in sorted(data.climate_devices.items()):
        diagnostic_fields = getattr(device, "diagnostic_fields", None)
        if not isinstance(diagnostic_fields, dict):
            diagnostic_fields = {}

        devices[device_id] = {
            "model": getattr(device, "model", None),
            "available": getattr(device, "available", None),
            "field_count": len(diagnostic_fields),
            "present_fields": sorted(diagnostic_fields),
            "normalized_fields": _normalized_climate_fields(device),
            "support_fields": {
                field: diagnostic_fields.get(field)
                for field in CLIMATE_SUPPORT_FIELDS
                if field in diagnostic_fields
            },
        }

    return {"devices": devices}


def _normalized_climate_fields(device: Any) -> dict[str, Any]:
    """Return normalized climate fields for diagnostics."""
    fields = {field: getattr(device, field, None) for field in CLIMATE_NORMALIZED_FIELDS}
    fields.update(
        {
            field: list(getattr(device, field, None) or [])
            for field in CLIMATE_NORMALIZED_SEQUENCE_FIELDS
        }
    )
    fields.update(
        {
            field: None
            if getattr(device, field, None) is None
            else list(getattr(device, field, None) or [])
            for field in CLIMATE_NORMALIZED_OPTIONAL_SEQUENCE_FIELDS
        }
    )
    return fields
