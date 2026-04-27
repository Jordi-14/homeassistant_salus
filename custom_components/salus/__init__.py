"""Support for Salus iT600."""
import json
import logging
import time
from asyncio import sleep
from types import MethodType

from homeassistant import config_entries, core
from homeassistant.helpers import device_registry as dr

from homeassistant.const import (
    CONF_HOST,
    CONF_TOKEN
)

from pyit600.exceptions import IT600AuthenticationError, IT600ConnectionError
from pyit600.gateway import IT600Gateway
from pyit600.const import (
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
from pyit600.models import ClimateDevice

from .config_flow import CONF_FLOW_TYPE, CONF_USER
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

GATEWAY_PLATFORMS = ["climate", "binary_sensor", "switch", "cover", "sensor"]
DEFAULT_HOLD_TYPE = 2
DEFAULT_RUNNING_STATE = 0


def _device_name(device_status, unique_id):
    """Return the Salus device name from a raw gateway payload."""
    default_name = {"deviceName": unique_id or "Unknown"}
    raw_name = device_status.get("sZDO", {}).get("DeviceName", json.dumps(default_name))
    try:
        return json.loads(raw_name)["deviceName"]
    except (KeyError, TypeError, ValueError):
        return default_name["deviceName"]


def _hold_type(device_status, unique_id):
    """Return HoldType, defaulting broken payloads to permanent hold."""
    th = device_status.get("sIT600TH", {})
    if "HoldType" not in th:
        warned = getattr(_LOGGER, "_salus_missing_hold_type_warned", set())
        if unique_id not in warned:
            _LOGGER.warning(
                "Salus climate device %s is missing HoldType in the gateway payload; "
                "treating it as Permanent Hold so Home Assistant can load it",
                unique_id,
            )
            warned.add(unique_id)
            setattr(_LOGGER, "_salus_missing_hold_type_warned", warned)
    return th.get("HoldType", DEFAULT_HOLD_TYPE)


async def _refresh_climate_devices_with_missing_hold_type(self, devices, send_callback=False):
    """Refresh pyit600 climate devices while tolerating missing HoldType."""
    local_devices = {}

    if devices:
        status = await self._make_encrypted_request(
            "read",
            {
                "requestAttr": "deviceid",
                "id": [{"data": device["data"]} for device in devices]
            }
        )

        for device_status in status["id"]:
            unique_id = device_status.get("data", {}).get("UniID", None)
            if unique_id is None:
                continue

            try:
                model = device_status.get("DeviceL", {}).get("ModelIdentifier_i", None)
                th = device_status.get("sIT600TH", None)
                ther = device_status.get("sTherS", None)
                scomm = device_status.get("sComm", None)
                sfans = device_status.get("sFanS", None)
                global_args = {
                    "available": device_status.get("sZDOInfo", {}).get("OnlineStatus_i", 1) == 1,
                    "name": _device_name(device_status, unique_id),
                    "unique_id": unique_id,
                    "temperature_unit": TEMP_CELSIUS,
                    "precision": 0.1,
                    "device_class": "temperature",
                    "data": device_status["data"],
                    "manufacturer": device_status.get("sBasicS", {}).get("ManufactureName", "SALUS"),
                    "model": model,
                    "sw_version": device_status.get("sZDO", {}).get("FirmwareVersion", None),
                }

                if th is not None:
                    current_humidity = None
                    if model is not None and "SQ610" in model:
                        current_humidity = th.get("SunnySetpoint_x100", None)

                    hold_type = _hold_type(device_status, unique_id)
                    running_state = th.get("RunningState", DEFAULT_RUNNING_STATE)
                    device = ClimateDevice(
                        **global_args,
                        current_humidity=current_humidity,
                        current_temperature=th["LocalTemperature_x100"] / 100,
                        target_temperature=th["HeatingSetpoint_x100"] / 100,
                        max_temp=th.get("MaxHeatSetpoint_x100", 3500) / 100,
                        min_temp=th.get("MinHeatSetpoint_x100", 500) / 100,
                        hvac_mode=HVAC_MODE_OFF if hold_type == 7 else HVAC_MODE_HEAT if hold_type == 2 else HVAC_MODE_AUTO,
                        hvac_action=CURRENT_HVAC_OFF if hold_type == 7 else CURRENT_HVAC_IDLE if running_state % 2 == 0 else CURRENT_HVAC_HEAT,
                        hvac_modes=[HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_AUTO],
                        preset_mode=PRESET_OFF if hold_type == 7 else PRESET_PERMANENT_HOLD if hold_type == 2 else PRESET_FOLLOW_SCHEDULE,
                        preset_modes=[PRESET_FOLLOW_SCHEDULE, PRESET_PERMANENT_HOLD, PRESET_OFF],
                        fan_mode=None,
                        fan_modes=None,
                        locked=None,
                        supported_features=SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE,
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
                        target_temperature=(ther["HeatingSetpoint_x100"] / 100) if is_heating else (ther["CoolingSetpoint_x100"] / 100),
                        max_temp=(ther.get("MaxHeatSetpoint_x100", 4000) / 100) if is_heating else (ther.get("MaxCoolSetpoint_x100", 4000) / 100),
                        min_temp=(ther.get("MinHeatSetpoint_x100", 500) / 100) if is_heating else (ther.get("MinCoolSetpoint_x100", 500) / 100),
                        hvac_mode=HVAC_MODE_HEAT if ther["SystemMode"] == 4 else HVAC_MODE_COOL if ther["SystemMode"] == 3 else HVAC_MODE_AUTO,
                        hvac_action=CURRENT_HVAC_OFF if hold_type == 7 else CURRENT_HVAC_IDLE if running_state == 0 else CURRENT_HVAC_HEAT if is_heating and running_state == 33 else CURRENT_HVAC_HEAT_IDLE if is_heating else CURRENT_HVAC_COOL if running_state == 66 else CURRENT_HVAC_COOL_IDLE,
                        hvac_modes=[HVAC_MODE_HEAT, HVAC_MODE_COOL, HVAC_MODE_AUTO],
                        preset_mode=PRESET_OFF if hold_type == 7 else PRESET_PERMANENT_HOLD if hold_type == 2 else PRESET_ECO if hold_type == 10 else PRESET_TEMPORARY_HOLD if hold_type == 1 else PRESET_FOLLOW_SCHEDULE,
                        preset_modes=[PRESET_OFF, PRESET_PERMANENT_HOLD, PRESET_ECO, PRESET_TEMPORARY_HOLD, PRESET_FOLLOW_SCHEDULE],
                        fan_mode=FAN_MODE_OFF if fan_mode == 0 else FAN_MODE_HIGH if fan_mode == 3 else FAN_MODE_MEDIUM if fan_mode == 2 else FAN_MODE_LOW if fan_mode == 1 else FAN_MODE_AUTO,
                        fan_modes=[FAN_MODE_AUTO, FAN_MODE_HIGH, FAN_MODE_MEDIUM, FAN_MODE_LOW, FAN_MODE_OFF],
                        locked=device_status.get("sTherUIS", {}).get("LockKey", 0) == 1,
                        supported_features=SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE | SUPPORT_FAN_MODE,
                    )
                else:
                    continue

                local_devices[device.unique_id] = device
                if send_callback:
                    self._climate_devices[device.unique_id] = device
                    await self._send_climate_update_callback(device_id=device.unique_id)
            except BaseException as e:
                _LOGGER.error("Failed to poll device %s", unique_id, exc_info=e)

    self._climate_devices = local_devices
    _LOGGER.debug("Refreshed %s climate devices", len(self._climate_devices))


def _patch_gateway(gateway):
    """Patch pyit600 for Salus payloads that omit HoldType."""
    gateway._refresh_climate_devices = MethodType(  # noqa: SLF001
        _refresh_climate_devices_with_missing_hold_type,
        gateway,
    )


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Salus iT600 component."""
    return True


async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up components from a config entry."""
    hass.data[DOMAIN] = {}
    if entry.data[CONF_FLOW_TYPE] == CONF_USER:
        if not await async_setup_gateway_entry(hass, entry):
            return False

    return True


async def async_setup_gateway_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up the Gateway component from a config entry."""
    host = entry.data[CONF_HOST]
    euid = entry.data[CONF_TOKEN]

    # Connect to gateway
    gateway = IT600Gateway(host=host, euid=euid)
    _patch_gateway(gateway)
    try:
        for remaining_attempts in reversed(range(3)):
            try:
                await gateway.connect()
                await gateway.poll_status()
            except Exception as e:
                if remaining_attempts == 0:
                    raise e
                else:
                    await sleep(3)
    except IT600ConnectionError as ce:
        _LOGGER.error("Connection error: check if you have specified gateway's HOST correctly.")
        return False
    except IT600AuthenticationError as ae:
        _LOGGER.error("Authentication error: check if you have specified gateway's EUID correctly.")
        return False

    hass.data[DOMAIN][entry.entry_id] = gateway

    gateway_info = gateway.get_gateway_device()

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, gateway_info.unique_id)},
        identifiers={(DOMAIN, gateway_info.unique_id)},
        manufacturer=gateway_info.manufacturer,
        name=gateway_info.name,
        model=gateway_info.model,
        sw_version=gateway_info.sw_version,
    )

    await hass.config_entries.async_forward_entry_setups(entry, GATEWAY_PLATFORMS)

    return True

async def async_unload_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, GATEWAY_PLATFORMS
    )

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok
