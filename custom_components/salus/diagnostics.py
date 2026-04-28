"""Diagnostics support for the Salus iT600 integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SalusData, SalusRuntimeData

TO_REDACT = {CONF_TOKEN}

SQ610_SUPPORT_FIELDS = (
    "UniID",
    "DeviceName",
    "ModelIdentifier_i",
    "OnlineStatus_i",
    "FirmwareVersion",
    "LocalTemperature_x100",
    "MeasuredValue_x100",
    "HeatingSetpoint_x100",
    "CoolingSetpoint_x100",
    "SunnySetpoint_x100",
    "SystemMode",
    "RunningState",
    "HoldType",
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a Salus config entry."""
    runtime_data = _runtime_data(hass, entry)

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
            "gateway": {
                "id": coordinator.gateway_id,
                "host": getattr(entry, "data", {}).get(CONF_HOST),
                "health": coordinator.gateway_diagnostics(),
            },
            "device_counts": _device_counts(data),
            "device_availability": coordinator.device_availability_diagnostics(),
            "sq610": _sq610_diagnostics(data),
        }
    )
    return diagnostics


def _runtime_data(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> SalusRuntimeData | None:
    """Return runtime data from modern or fallback Home Assistant storage."""
    runtime_data = getattr(entry, "runtime_data", None)
    if runtime_data is not None:
        return runtime_data

    domain_data = getattr(hass, "data", {}).get(DOMAIN, {})
    return domain_data.get(getattr(entry, "entry_id", None))


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


def _sq610_diagnostics(data: SalusData | None) -> dict[str, Any]:
    """Return SQ610 raw-property diagnostics useful for field support."""
    if data is None:
        return {"devices": {}}

    devices: dict[str, Any] = {}
    for device_id, raw_props in sorted(data.raw_climate_props.items()):
        devices[device_id] = {
            "field_count": len(raw_props),
            "present_fields": sorted(raw_props),
            "support_fields": {
                field: raw_props.get(field)
                for field in SQ610_SUPPORT_FIELDS
                if field in raw_props
            },
        }

    return {"devices": devices}
