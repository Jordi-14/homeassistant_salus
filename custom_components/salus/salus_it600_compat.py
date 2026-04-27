"""Compatibility patches for salus_it600 gateway payload variations."""

from __future__ import annotations

import json
import logging
from types import MethodType
from typing import Any

from salus_it600.const import (
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_COOL_IDLE,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_HEAT_IDLE,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
    FAN_MODE_AUTO,
    FAN_MODE_HIGH,
    FAN_MODE_LOW,
    FAN_MODE_MEDIUM,
    FAN_MODE_OFF,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_ECO,
    PRESET_FOLLOW_SCHEDULE,
    PRESET_OFF,
    PRESET_PERMANENT_HOLD,
    PRESET_TEMPORARY_HOLD,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    TEMP_CELSIUS,
)
from salus_it600.models import ClimateDevice

_LOGGER = logging.getLogger(__name__)

DEFAULT_HOLD_TYPE = 2
DEFAULT_RUNNING_STATE = 0
_MISSING_HOLD_TYPE_WARNED: set[str] = set()


def _device_name(device_status: dict[str, Any], unique_id: str | None) -> str:
    """Return the Salus device name from a raw gateway payload."""
    default_name = {"deviceName": unique_id or "Unknown"}
    raw_name = device_status.get("sZDO", {}).get("DeviceName", json.dumps(default_name))

    try:
        return json.loads(raw_name)["deviceName"]
    except (KeyError, TypeError, ValueError):
        return default_name["deviceName"]


def _hold_type(device_status: dict[str, Any], unique_id: str) -> int:
    """Return HoldType, defaulting broken payloads to permanent hold."""
    th = device_status.get("sIT600TH", {})
    if "HoldType" not in th:
        if unique_id not in _MISSING_HOLD_TYPE_WARNED:
            _LOGGER.warning(
                "Salus climate device %s is missing HoldType in the gateway payload; "
                "treating it as Permanent Hold so Home Assistant can load it",
                unique_id,
            )
            _MISSING_HOLD_TYPE_WARNED.add(unique_id)
    return th.get("HoldType", DEFAULT_HOLD_TYPE)


async def _refresh_climate_devices_with_missing_hold_type(
    self: Any,
    devices: list[dict[str, Any]],
    send_callback: bool = False,
) -> None:
    """Refresh salus_it600 climate devices while tolerating missing HoldType."""
    local_devices = {}

    if devices:
        status = await self._make_encrypted_request(  # noqa: SLF001
            "read",
            {
                "requestAttr": "deviceid",
                "id": [{"data": device["data"]} for device in devices],
            },
        )

        for device_status in status["id"]:
            unique_id = device_status.get("data", {}).get("UniID")
            if unique_id is None:
                continue

            try:
                model = device_status.get("DeviceL", {}).get("ModelIdentifier_i")
                th = device_status.get("sIT600TH")
                ther = device_status.get("sTherS")
                scomm = device_status.get("sComm")
                sfans = device_status.get("sFanS")
                global_args = {
                    "available": device_status.get("sZDOInfo", {}).get(
                        "OnlineStatus_i", 1
                    )
                    == 1,
                    "name": _device_name(device_status, unique_id),
                    "unique_id": unique_id,
                    "temperature_unit": TEMP_CELSIUS,
                    "precision": 0.1,
                    "device_class": "temperature",
                    "data": device_status["data"],
                    "manufacturer": device_status.get("sBasicS", {}).get(
                        "ManufactureName", "SALUS"
                    ),
                    "model": model,
                    "sw_version": device_status.get("sZDO", {}).get(
                        "FirmwareVersion"
                    ),
                }

                if th is not None:
                    current_humidity = None
                    if model is not None and "SQ610" in model:
                        current_humidity = th.get("SunnySetpoint_x100")

                    hold_type = _hold_type(device_status, unique_id)
                    running_state = th.get("RunningState", DEFAULT_RUNNING_STATE)
                    device = ClimateDevice(
                        **global_args,
                        current_humidity=current_humidity,
                        current_temperature=th["LocalTemperature_x100"] / 100,
                        target_temperature=th["HeatingSetpoint_x100"] / 100,
                        max_temp=th.get("MaxHeatSetpoint_x100", 3500) / 100,
                        min_temp=th.get("MinHeatSetpoint_x100", 500) / 100,
                        hvac_mode=HVAC_MODE_OFF
                        if hold_type == 7
                        else HVAC_MODE_HEAT
                        if hold_type == 2
                        else HVAC_MODE_AUTO,
                        hvac_action=CURRENT_HVAC_OFF
                        if hold_type == 7
                        else CURRENT_HVAC_IDLE
                        if running_state % 2 == 0
                        else CURRENT_HVAC_HEAT,
                        hvac_modes=[HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_AUTO],
                        preset_mode=PRESET_OFF
                        if hold_type == 7
                        else PRESET_PERMANENT_HOLD
                        if hold_type == 2
                        else PRESET_FOLLOW_SCHEDULE,
                        preset_modes=[
                            PRESET_FOLLOW_SCHEDULE,
                            PRESET_PERMANENT_HOLD,
                            PRESET_OFF,
                        ],
                        fan_mode=None,
                        fan_modes=None,
                        locked=None,
                        supported_features=SUPPORT_TARGET_TEMPERATURE
                        | SUPPORT_PRESET_MODE,
                    )
                elif ther is not None and scomm is not None and sfans is not None:
                    is_heating = ther["SystemMode"] == 4
                    fan_mode = sfans.get("FanMode", 5)
                    hold_type = scomm.get("HoldType", DEFAULT_HOLD_TYPE)
                    running_state = ther.get("RunningState", DEFAULT_RUNNING_STATE)
                    device = ClimateDevice(
                        **global_args,
                        current_humidity=None,
                        current_temperature=ther["LocalTemperature_x100"] / 100,
                        target_temperature=(
                            ther["HeatingSetpoint_x100"] / 100
                            if is_heating
                            else ther["CoolingSetpoint_x100"] / 100
                        ),
                        max_temp=(
                            ther.get("MaxHeatSetpoint_x100", 4000) / 100
                            if is_heating
                            else ther.get("MaxCoolSetpoint_x100", 4000) / 100
                        ),
                        min_temp=(
                            ther.get("MinHeatSetpoint_x100", 500) / 100
                            if is_heating
                            else ther.get("MinCoolSetpoint_x100", 500) / 100
                        ),
                        hvac_mode=HVAC_MODE_HEAT
                        if ther["SystemMode"] == 4
                        else HVAC_MODE_COOL
                        if ther["SystemMode"] == 3
                        else HVAC_MODE_AUTO,
                        hvac_action=CURRENT_HVAC_OFF
                        if hold_type == 7
                        else CURRENT_HVAC_IDLE
                        if running_state == 0
                        else CURRENT_HVAC_HEAT
                        if is_heating and running_state == 33
                        else CURRENT_HVAC_HEAT_IDLE
                        if is_heating
                        else CURRENT_HVAC_COOL
                        if running_state == 66
                        else CURRENT_HVAC_COOL_IDLE,
                        hvac_modes=[HVAC_MODE_HEAT, HVAC_MODE_COOL, HVAC_MODE_AUTO],
                        preset_mode=PRESET_OFF
                        if hold_type == 7
                        else PRESET_PERMANENT_HOLD
                        if hold_type == 2
                        else PRESET_ECO
                        if hold_type == 10
                        else PRESET_TEMPORARY_HOLD
                        if hold_type == 1
                        else PRESET_FOLLOW_SCHEDULE,
                        preset_modes=[
                            PRESET_OFF,
                            PRESET_PERMANENT_HOLD,
                            PRESET_ECO,
                            PRESET_TEMPORARY_HOLD,
                            PRESET_FOLLOW_SCHEDULE,
                        ],
                        fan_mode=FAN_MODE_OFF
                        if fan_mode == 0
                        else FAN_MODE_HIGH
                        if fan_mode == 3
                        else FAN_MODE_MEDIUM
                        if fan_mode == 2
                        else FAN_MODE_LOW
                        if fan_mode == 1
                        else FAN_MODE_AUTO,
                        fan_modes=[
                            FAN_MODE_AUTO,
                            FAN_MODE_HIGH,
                            FAN_MODE_MEDIUM,
                            FAN_MODE_LOW,
                            FAN_MODE_OFF,
                        ],
                        locked=device_status.get("sTherUIS", {}).get("LockKey", 0)
                        == 1,
                        supported_features=SUPPORT_TARGET_TEMPERATURE
                        | SUPPORT_PRESET_MODE
                        | SUPPORT_FAN_MODE,
                    )
                else:
                    continue

                local_devices[device.unique_id] = device
                if send_callback:
                    self._climate_devices[device.unique_id] = device
                    await self._send_climate_update_callback(
                        device_id=device.unique_id
                    )
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Failed to poll device %s", unique_id)

    self._climate_devices = local_devices
    _LOGGER.debug("Refreshed %s climate devices", len(self._climate_devices))


def patch_gateway(gateway: Any) -> None:
    """Patch salus_it600 for Salus payloads that omit HoldType."""
    gateway._refresh_climate_devices = MethodType(  # noqa: SLF001
        _refresh_climate_devices_with_missing_hold_type,
        gateway,
    )
