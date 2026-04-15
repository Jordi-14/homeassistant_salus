"""Support for climate devices (thermostats)."""
from datetime import timedelta
import logging
import async_timeout

import voluptuous as vol
from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
    FAN_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_HOST,
    CONF_TOKEN
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

RAW_PRESET_FOLLOW_SCHEDULE = "Follow Schedule"
RAW_PRESET_PERMANENT_HOLD = "Permanent Hold"
RAW_PRESET_TEMPORARY_HOLD = "Temporary Hold"
RAW_PRESET_ECO = "Eco"
RAW_PRESET_OFF = "Off"

PRESET_STANDBY = "Standby"
EXPOSED_PRESET_MODES = [RAW_PRESET_PERMANENT_HOLD, PRESET_STANDBY]

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

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): cv.string,
    }
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Salus thermostats from a config entry."""

    gateway = hass.data[DOMAIN][config_entry.entry_id]

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        async with async_timeout.timeout(10):
            await gateway.poll_status()
            return gateway.get_climate_devices()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="sensor",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=30),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_entities(SalusThermostat(coordinator, idx, gateway) for idx
                       in coordinator.data)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    pass


class SalusThermostat(ClimateEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, idx, gateway):
        """Initialize the thermostat."""
        self._coordinator = coordinator
        self._idx = idx
        self._gateway = gateway

    @property
    def _device(self):
        """Return the latest thermostat snapshot from the coordinator."""
        return self._coordinator.data.get(self._idx)

    @property
    def _supports_cooling(self):
        """Return whether the thermostat exposes a separate cooling mode."""
        device = self._device
        return bool(
            device
            and (
                device.model == "FC600"
                or HVACMode.COOL in (device.hvac_modes or [])
                or device.fan_modes is not None
            )
        )

    @property
    def _effective_hvac_mode(self):
        """Return the Salus system mode we want to expose in Home Assistant."""
        device = self._device
        if device is None:
            return HVACMode.HEAT

        if device.hvac_mode == HVACMode.COOL:
            return HVACMode.COOL
        if device.hvac_mode == HVACMode.HEAT:
            return HVACMode.HEAT
        if self._supports_cooling and device.hvac_action in COOLING_ACTIONS:
            return HVACMode.COOL
        return HVACMode.HEAT

    @property
    def _effective_preset_mode(self):
        """Collapse Salus hold states into the smaller HA control surface."""
        device = self._device
        if device is None:
            return None

        if device.preset_mode == RAW_PRESET_OFF:
            return PRESET_STANDBY
        if device.preset_mode in MANUAL_PRESET_MODES:
            return RAW_PRESET_PERMANENT_HOLD
        if device.preset_mode == RAW_PRESET_FOLLOW_SCHEDULE:
            return None
        return device.preset_mode

    async def async_update(self):
        """Update the entity.
        Only used by the generic entity update service.
        """
        await self._coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )
    
    @property
    def supported_features(self):
        """Return the list of supported features."""
        supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
        )
        if self._device.fan_modes is not None:
            supported_features |= ClimateEntityFeature.FAN_MODE
        return supported_features

    @property
    def available(self):
        """Return if entity is available."""
        return self._device.available

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "name": self._device.name,
            "identifiers": {("salus", self._device.unique_id)},
            "manufacturer": self._device.manufacturer,
            "model": self._device.model,
            "sw_version": self._device.sw_version
        }

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._device.unique_id

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def name(self):
        """Return the name of the Radio Thermostat."""
        return self._device.name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._device.temperature_unit

    @property
    def precision(self):
        """Return the precision of the system."""
        return self._device.precision

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.current_temperature

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._device.current_humidity

    @property
    def hvac_mode(self):
        """Return the current operation. head, cool idle."""
        return self._effective_hvac_mode

    @property
    def hvac_modes(self):
        """Return the operation modes list."""
        if self._supports_cooling:
            return [HVACMode.HEAT, HVACMode.COOL]
        return [HVACMode.HEAT]

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported."""
        return self._device.hvac_action

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._device.target_temperature

    @property
    def max_temp(self):
        return self._device.max_temp

    @property
    def min_temp(self):
        return self._device.min_temp

    @property
    def preset_mode(self):
        return self._effective_preset_mode

    @property
    def preset_modes(self):
        return EXPOSED_PRESET_MODES

    @property
    def fan_mode(self):
        return RAW_TO_HA_FAN_MODE.get(self._device.fan_mode)

    @property
    def fan_modes(self):
        if self._device.fan_modes is None:
            return None
        return [
            RAW_TO_HA_FAN_MODE[fan_mode]
            for fan_mode in self._device.fan_modes
            if fan_mode in RAW_TO_HA_FAN_MODE
        ]

    @property
    def locked(self):
        return self._device.locked

    @property
    def extra_state_attributes(self):
        """Expose the raw Salus state while the HA controls stay simplified."""
        return {
            "salus_raw_hvac_mode": self._device.hvac_mode,
            "salus_raw_preset_mode": self._device.preset_mode,
        }

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self._gateway.set_climate_device_temperature(self._idx, temperature)
        await self._coordinator.async_request_refresh()

    # TODO: Not listed in methods here https://developers.home-assistant.io/docs/core/entity/climate/#methods
    # async def async_set_locked(self, locked):
    #     """Set locked (true, false)."""
    #     await self._gateway.set_climate_device_locked(self._idx, locked)
    #     await self._coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode):
        """Set fan speed (auto, low, medium, high, off)."""
        mode = HA_TO_RAW_FAN_MODE.get(fan_mode)
        if mode is None:
            _LOGGER.warning("Unsupported fan mode requested for %s: %s", self._idx, fan_mode)
            return
        await self._gateway.set_climate_device_fan_mode(self._idx, mode)
        await self._coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set operation mode."""
        if hvac_mode == HVACMode.OFF:
            await self.async_set_preset_mode(PRESET_STANDBY)
            return
        if hvac_mode == HVACMode.AUTO:
            _LOGGER.warning("Ignoring unsupported schedule mode request for %s", self._idx)
            return
        if hvac_mode not in self.hvac_modes:
            _LOGGER.warning("Ignoring unsupported HVAC mode request for %s: %s", self._idx, hvac_mode)
            return
        if not self._supports_cooling:
            return
        mode = hvac_mode
        await self._gateway.set_climate_device_mode(self._idx, mode)
        await self._coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode):
        """Set the exposed Salus hold mode."""
        if preset_mode == PRESET_STANDBY:
            raw_preset_mode = RAW_PRESET_OFF
        elif preset_mode == RAW_PRESET_PERMANENT_HOLD:
            raw_preset_mode = RAW_PRESET_PERMANENT_HOLD
        else:
            _LOGGER.warning("Ignoring unsupported preset mode request for %s: %s", self._idx, preset_mode)
            return
        await self._gateway.set_climate_device_preset(self._idx, raw_preset_mode)
        await self._coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the thermostat on by resuming manual hold."""
        await self.async_set_preset_mode(RAW_PRESET_PERMANENT_HOLD)

    async def async_turn_off(self) -> None:
        """Turn the thermostat off by putting it in standby."""
        await self.async_set_preset_mode(PRESET_STANDBY)
