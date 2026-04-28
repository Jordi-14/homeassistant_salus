"""Support for Salus climate devices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from salus_it600.device_models import (
    SQ610_HOLD_AUTO,
    SQ610_HOLD_PERMANENT,
    SQ610_HOLD_STANDBY,
    SQ610_MODE_COOL,
    SQ610_MODE_HEAT,
    SQ610_WRITE_COOLING_SETPOINT,
    SQ610_WRITE_HEATING_SETPOINT,
    SQ610_WRITE_HOLD_TYPE,
    SQ610_WRITE_SYSTEM_MODE,
)

from ._climate_state import (
    HA_TO_RAW_FAN_MODE,
    PRESET_FOLLOW_SALUS_SCHEDULE,
    PRESET_STANDBY,
    RAW_PRESET_FOLLOW_SCHEDULE,
    RAW_PRESET_OFF,
    RAW_PRESET_PERMANENT_HOLD,
    ClimateViewState,
    build_climate_view_state,
)
from .coordinator import SalusData, SalusRuntimeData, is_sq610_device
from .entity import SalusEntity, async_add_salus_entities

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Salus thermostats from a config entry."""
    runtime_data: SalusRuntimeData = config_entry.runtime_data
    coordinator = runtime_data.coordinator

    async_add_salus_entities(
        config_entry,
        coordinator,
        async_add_entities,
        lambda device_id: SalusThermostat(coordinator, device_id),
        lambda data: data.climate_devices,
    )


class SalusThermostat(SalusEntity, ClimateEntity):
    """Representation of a Salus thermostat."""

    _enable_turn_on_off_backwards_compatibility = False

    @property
    def _device(self) -> Any | None:
        """Return the latest thermostat snapshot from the coordinator."""
        data: SalusData | None = self.coordinator.data
        return None if data is None else data.climate_devices.get(self._device_id)

    @property
    def _raw_props(self) -> dict[str, Any]:
        """Return the raw gateway properties for SQ610 devices."""
        data: SalusData | None = self.coordinator.data
        if data is None:
            return {}
        return data.raw_climate_props.get(self._device_id, {})

    @property
    def _is_sq610(self) -> bool:
        """Return whether the thermostat is a Quantum model."""
        return is_sq610_device(self._device)

    @property
    def _view(self) -> ClimateViewState:
        """Return the Home Assistant-facing climate view state."""
        return build_climate_view_state(self._device, self._raw_props)

    @property
    def _supports_cooling(self) -> bool:
        """Return whether the thermostat exposes a separate cooling mode."""
        return self._view.supports_cooling

    @property
    def _effective_hvac_mode(self) -> HVACMode:
        """Return the Salus system mode we want to expose in Home Assistant."""
        return self._view.hvac_mode

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return self._view.supported_features

    @property
    def temperature_unit(self) -> str | None:
        """Return the unit of measurement."""
        return None if self._device is None else self._device.temperature_unit

    @property
    def precision(self) -> float | None:
        """Return the precision of the system."""
        return None if self._device is None else self._device.precision

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._view.current_temperature

    @property
    def current_humidity(self) -> float | None:
        """Return the current humidity."""
        return self._view.current_humidity

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current operation mode."""
        return self._effective_hvac_mode

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the supported operation modes."""
        return self._view.hvac_modes

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current HVAC action if supported."""
        return self._view.hvac_action

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature the thermostat tries to reach."""
        return self._view.target_temperature

    @property
    def max_temp(self) -> float | None:
        """Return the maximum target temperature."""
        return None if self._device is None else self._device.max_temp

    @property
    def min_temp(self) -> float | None:
        """Return the minimum target temperature."""
        return None if self._device is None else self._device.min_temp

    @property
    def preset_mode(self) -> str | None:
        """Return the active preset mode."""
        return self._view.preset_mode

    @property
    def preset_modes(self) -> list[str]:
        """Return supported preset modes."""
        return self._view.preset_modes

    @property
    def fan_mode(self) -> str | None:
        """Return the active fan mode."""
        return self._view.fan_mode

    @property
    def fan_modes(self) -> list[str] | None:
        """Return supported fan modes."""
        return self._view.fan_modes

    @property
    def locked(self) -> bool | None:
        """Return if the thermostat is locked."""
        return None if self._device is None else self._device.locked

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the raw Salus state while the HA controls stay simplified."""
        device = self._device
        if device is None:
            return {}

        return {
            "salus_raw_hvac_mode": device.hvac_mode,
            "salus_raw_preset_mode": device.preset_mode,
            "salus_raw_system_mode": self._raw_props.get("SystemMode"),
            "salus_raw_running_state": self._raw_props.get("RunningState"),
            "salus_raw_hold_type": self._raw_props.get("HoldType"),
        }

    async def _async_write_sq610_property(self, prop: str, value: int) -> None:
        """Write a raw SQ610 property directly through the gateway API."""
        device = self._device
        if device is None:
            return

        async with self.coordinator.gateway_lock:
            await self.coordinator.gateway.write_sq610_property(
                self._device_id,
                prop,
                value,
            )
        await self.coordinator.async_request_debounced_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        if self._is_sq610:
            prop = (
                SQ610_WRITE_COOLING_SETPOINT
                if self._effective_hvac_mode == HVACMode.COOL
                else SQ610_WRITE_HEATING_SETPOINT
            )
            rounded_temperature = int(round(temperature * 2) / 2 * 100)
            await self._async_write_sq610_property(prop, rounded_temperature)
            return

        async with self.coordinator.gateway_lock:
            await self.coordinator.gateway.set_climate_device_temperature(
                self._device_id,
                temperature,
            )
        await self.coordinator.async_request_debounced_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan speed."""
        if self._is_sq610:
            return

        mode = HA_TO_RAW_FAN_MODE.get(fan_mode)
        if mode is None:
            _LOGGER.warning(
                "Ignoring unsupported fan mode request for %s: %s",
                self._device_id,
                fan_mode,
            )
            return

        async with self.coordinator.gateway_lock:
            await self.coordinator.gateway.set_climate_device_fan_mode(
                self._device_id,
                mode,
            )
        await self.coordinator.async_request_debounced_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set operation mode."""
        if hvac_mode == HVACMode.OFF:
            await self.async_set_preset_mode(PRESET_STANDBY)
            return
        if hvac_mode == HVACMode.AUTO:
            _LOGGER.warning(
                "Ignoring unsupported schedule mode request for %s",
                self._device_id,
            )
            return
        if hvac_mode not in self.hvac_modes:
            _LOGGER.warning(
                "Ignoring unsupported HVAC mode request for %s: %s",
                self._device_id,
                hvac_mode,
            )
            return

        if self._is_sq610:
            system_mode = (
                SQ610_MODE_COOL if hvac_mode == HVACMode.COOL else SQ610_MODE_HEAT
            )
            await self._async_write_sq610_property(SQ610_WRITE_SYSTEM_MODE, system_mode)
            return

        if not self._supports_cooling:
            return

        async with self.coordinator.gateway_lock:
            await self.coordinator.gateway.set_climate_device_mode(
                self._device_id,
                hvac_mode,
            )
        await self.coordinator.async_request_debounced_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the exposed Salus hold mode."""
        if preset_mode == PRESET_STANDBY:
            if self._is_sq610:
                await self._async_write_sq610_property(
                    SQ610_WRITE_HOLD_TYPE,
                    SQ610_HOLD_STANDBY,
                )
                return
            raw_preset_mode = RAW_PRESET_OFF
        elif preset_mode == RAW_PRESET_PERMANENT_HOLD:
            if self._is_sq610:
                await self._async_write_sq610_property(
                    SQ610_WRITE_HOLD_TYPE,
                    SQ610_HOLD_PERMANENT,
                )
                return
            raw_preset_mode = RAW_PRESET_PERMANENT_HOLD
        elif preset_mode == PRESET_FOLLOW_SALUS_SCHEDULE:
            if self._is_sq610:
                await self._async_write_sq610_property(
                    SQ610_WRITE_HOLD_TYPE,
                    SQ610_HOLD_AUTO,
                )
                return
            raw_preset_mode = RAW_PRESET_FOLLOW_SCHEDULE
        else:
            _LOGGER.warning(
                "Ignoring unsupported preset mode request for %s: %s",
                self._device_id,
                preset_mode,
            )
            return

        async with self.coordinator.gateway_lock:
            await self.coordinator.gateway.set_climate_device_preset(
                self._device_id,
                raw_preset_mode,
            )
        await self.coordinator.async_request_debounced_refresh()

    async def async_turn_on(self) -> None:
        """Turn the thermostat on by resuming manual hold."""
        await self.async_set_preset_mode(RAW_PRESET_PERMANENT_HOLD)

    async def async_turn_off(self) -> None:
        """Turn the thermostat off by putting it in standby."""
        await self.async_set_preset_mode(PRESET_STANDBY)
