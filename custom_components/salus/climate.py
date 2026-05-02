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
    MODEL_FC600,
    SQ610_HOLD_AUTO,
    SQ610_HOLD_PERMANENT,
    SQ610_HOLD_STANDBY,
    SQ610_MODE_COOL,
    SQ610_RUNNING_COOL,
)

from ._climate_state import (
    HA_TO_RAW_FAN_MODE,
    PRESET_ECO,
    PRESET_FOLLOW_SCHEDULE,
    PRESET_PERMANENT_HOLD,
    PRESET_STANDBY,
    RAW_PRESET_ECO,
    RAW_PRESET_FOLLOW_SCHEDULE,
    RAW_PRESET_OFF,
    RAW_PRESET_PERMANENT_HOLD,
    RAW_PRESET_TEMPORARY_HOLD,
    ClimateCapabilities,
    ClimateViewState,
    build_climate_capabilities,
    build_climate_view_state,
)
from .coordinator import SalusData, SalusRuntimeData, is_sq610_device
from .entity import SalusEntity, async_add_salus_entities

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1

SQ610_RESUME_PRESET_TO_RAW = {
    PRESET_FOLLOW_SCHEDULE: RAW_PRESET_FOLLOW_SCHEDULE,
    PRESET_PERMANENT_HOLD: RAW_PRESET_PERMANENT_HOLD,
}
FC600_RESUME_PRESET_TO_RAW = {
    PRESET_FOLLOW_SCHEDULE: RAW_PRESET_FOLLOW_SCHEDULE,
    PRESET_PERMANENT_HOLD: RAW_PRESET_PERMANENT_HOLD,
    PRESET_ECO: RAW_PRESET_ECO,
}


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
    _attr_translation_key = "thermostat"

    def __init__(self, coordinator: Any, device_id: str) -> None:
        """Initialize a Salus thermostat entity."""
        super().__init__(coordinator, device_id)
        self._sq610_resume_preset_mode: str | None = None
        self._sq610_supports_cooling = False
        self._sq610_logged_unknown_hold_types: set[str] = set()
        self._fc600_resume_preset_mode: str | None = None

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
    def _is_fc600(self) -> bool:
        """Return whether the thermostat is an FC600 fan coil."""
        device = self._device
        return getattr(device, "model", None) == MODEL_FC600

    @property
    def _view(self) -> ClimateViewState:
        """Return the Home Assistant-facing climate view state."""
        resume_preset_mode = None
        known_supports_cooling = False
        fc600_resume_preset_mode = None
        if self._is_sq610:
            self._remember_sq610_cooling_support()
            self._remember_current_sq610_preset()
            resume_preset_mode = self._sq610_resume_preset_mode
            known_supports_cooling = self._sq610_supports_cooling
        if self._is_fc600:
            self._remember_current_fc600_preset()
            fc600_resume_preset_mode = self._fc600_resume_preset_mode
        return build_climate_view_state(
            self._device,
            self._raw_props,
            sq610_resume_preset_mode=resume_preset_mode,
            sq610_known_supports_cooling=known_supports_cooling,
            fc600_resume_preset_mode=fc600_resume_preset_mode,
        )

    @property
    def _capabilities(self) -> ClimateCapabilities:
        """Return the current Salus control capabilities for this device."""
        return build_climate_capabilities(
            self._device,
            self._raw_props,
            self._sq610_supports_cooling,
        )

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

        attributes = {
            "salus_raw_hvac_mode": device.hvac_mode,
            "salus_raw_preset_mode": device.preset_mode,
            "salus_raw_system_mode": self._raw_props.get("SystemMode"),
            "salus_raw_running_state": self._raw_props.get("RunningState"),
            "salus_raw_hold_type": self._raw_props.get("HoldType"),
        }
        extra = getattr(device, "extra_state_attributes", None)
        if isinstance(extra, dict):
            attributes.update(extra)
        return attributes

    async def _async_request_debounced_refresh_after_sq610_write(self) -> None:
        """Request a debounced refresh after an SQ610 command."""
        device = self._device
        if device is None:
            return

        await self.coordinator.async_request_debounced_refresh()

    def _current_sq610_preset_mode(self) -> str | None:
        """Return the active non-standby SQ610 preset from raw or parsed state."""
        hold_type = self._raw_props.get("HoldType")
        if hold_type == SQ610_HOLD_AUTO:
            return PRESET_FOLLOW_SCHEDULE
        if hold_type == SQ610_HOLD_PERMANENT:
            return PRESET_PERMANENT_HOLD
        if hold_type == SQ610_HOLD_STANDBY:
            return None
        if hold_type is not None:
            hold_type_key = repr(hold_type)
            if hold_type_key not in self._sq610_logged_unknown_hold_types:
                self._sq610_logged_unknown_hold_types.add(hold_type_key)
                _LOGGER.debug(
                    "Ignoring unknown SQ610 HoldType for %s: %s",
                    self._device_id,
                    hold_type,
                )
            return None

        device = self._device
        if device is None:
            return None

        preset_mode = getattr(device, "preset_mode", None)
        if preset_mode == RAW_PRESET_FOLLOW_SCHEDULE:
            return PRESET_FOLLOW_SCHEDULE
        if preset_mode == RAW_PRESET_PERMANENT_HOLD:
            return PRESET_PERMANENT_HOLD
        return None

    def _remember_current_sq610_preset(self) -> None:
        """Remember the last active hold/schedule preset for standby resume."""
        preset_mode = self._current_sq610_preset_mode()
        if preset_mode is not None:
            self._sq610_resume_preset_mode = preset_mode

    def _current_fc600_preset_mode(self) -> str | None:
        """Return the active non-off FC600 preset from parsed state."""
        device = self._device
        if device is None:
            return None

        preset_mode = getattr(device, "preset_mode", None)
        if preset_mode == RAW_PRESET_FOLLOW_SCHEDULE:
            return PRESET_FOLLOW_SCHEDULE
        if preset_mode == RAW_PRESET_ECO:
            return PRESET_ECO
        if preset_mode in {RAW_PRESET_PERMANENT_HOLD, RAW_PRESET_TEMPORARY_HOLD}:
            return PRESET_PERMANENT_HOLD
        return None

    def _remember_current_fc600_preset(self) -> None:
        """Remember the last active FC600 preset for off-state resume."""
        preset_mode = self._current_fc600_preset_mode()
        if preset_mode is not None:
            self._fc600_resume_preset_mode = preset_mode

    def _sq610_snapshot_supports_cooling(self) -> bool:
        """Return whether the current SQ610 snapshot proves cooling support."""
        raw_props = self._raw_props
        if (
            raw_props.get("SystemMode") == SQ610_MODE_COOL
            or raw_props.get("RunningState") == SQ610_RUNNING_COOL
            or raw_props.get("CoolingSetpoint_x100") is not None
        ):
            return True

        return False

    def _remember_sq610_cooling_support(self) -> None:
        """Keep Cool exposed after an SQ610 has proved cooling support once."""
        if self._sq610_snapshot_supports_cooling():
            self._sq610_supports_cooling = True

    @property
    def _sq610_resume_raw_preset_mode(self) -> str:
        """Return the raw Salus preset to restore when leaving SQ610 standby."""
        return SQ610_RESUME_PRESET_TO_RAW.get(
            self._sq610_resume_preset_mode,
            RAW_PRESET_PERMANENT_HOLD,
        )

    @property
    def _fc600_resume_raw_preset_mode(self) -> str:
        """Return the raw Salus preset to restore when leaving FC600 off."""
        return FC600_RESUME_PRESET_TO_RAW.get(
            self._fc600_resume_preset_mode,
            RAW_PRESET_PERMANENT_HOLD,
        )

    async def _async_set_sq610_raw_preset(self, raw_preset_mode: str) -> None:
        """Set an SQ610 raw preset and refresh state."""
        await self._async_run_gateway_command(
            "set SQ610 preset",
            lambda: self.coordinator.gateway.set_sq610_device_preset(
                self._device_id,
                raw_preset_mode,
            ),
        )
        await self._async_request_debounced_refresh_after_sq610_write()

    async def _async_set_fc600_raw_preset(self, raw_preset_mode: str) -> None:
        """Set an FC600 raw preset and refresh state."""
        await self._async_run_gateway_command(
            "set FC600 preset",
            lambda: self.coordinator.gateway.set_climate_device_preset(
                self._device_id,
                raw_preset_mode,
            ),
        )
        await self.coordinator.async_request_debounced_refresh()

    async def _async_set_generic_raw_preset(self, raw_preset_mode: str) -> None:
        """Set a standard Salus hold/preset value and refresh state."""
        await self._async_run_gateway_command(
            "set preset",
            lambda: self.coordinator.gateway.set_climate_device_preset(
                self._device_id,
                raw_preset_mode,
            ),
        )
        await self.coordinator.async_request_debounced_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        if self._is_sq610:
            if self._raw_props.get("HoldType") == SQ610_HOLD_STANDBY:
                _LOGGER.debug(
                    "Ignoring SQ610 target temperature change while %s is in standby",
                    self._device_id,
                )
                return
            await self._async_run_gateway_command(
                "set SQ610 target temperature",
                lambda: self.coordinator.gateway.set_sq610_device_temperature(
                    self._device_id,
                    temperature,
                    cooling=self._effective_hvac_mode == HVACMode.COOL,
                ),
            )
            await self._async_request_debounced_refresh_after_sq610_write()
            return

        if self._is_fc600 and self._device is not None:
            if self._device.preset_mode in {RAW_PRESET_OFF, RAW_PRESET_ECO}:
                _LOGGER.debug(
                    "Ignoring FC600 target temperature change while %s is in %s",
                    self._device_id,
                    self._device.preset_mode,
                )
                return

        await self._async_run_gateway_command(
            "set target temperature",
            lambda: self.coordinator.gateway.set_climate_device_temperature(
                self._device_id,
                temperature,
            ),
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

        await self._async_run_gateway_command(
            "set fan mode",
            lambda: self.coordinator.gateway.set_climate_device_fan_mode(
                self._device_id,
                mode,
            ),
        )
        await self.coordinator.async_request_debounced_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set operation mode."""
        if hvac_mode not in self.hvac_modes:
            _LOGGER.warning(
                "Ignoring unsupported HVAC mode request for %s: %s",
                self._device_id,
                hvac_mode,
            )
            return
        if hvac_mode == HVACMode.OFF:
            if self._is_sq610:
                self._remember_current_sq610_preset()
                await self._async_set_sq610_raw_preset(RAW_PRESET_OFF)
                return
            if self._is_fc600:
                self._remember_current_fc600_preset()
                await self._async_set_fc600_raw_preset(RAW_PRESET_OFF)
                return
            await self._async_set_generic_raw_preset(RAW_PRESET_OFF)
            return
        if hvac_mode == HVACMode.AUTO:
            await self._async_set_generic_raw_preset(RAW_PRESET_FOLLOW_SCHEDULE)
            return

        if self._is_sq610:
            restore_preset = self._raw_props.get("HoldType") == SQ610_HOLD_STANDBY
            raw_resume_preset = self._sq610_resume_raw_preset_mode

            async def set_sq610_mode() -> None:
                await self.coordinator.gateway.set_sq610_device_hvac_mode(
                    self._device_id,
                    hvac_mode,
                )
                if restore_preset:
                    await self.coordinator.gateway.set_sq610_device_preset(
                        self._device_id,
                        raw_resume_preset,
                    )

            await self._async_run_gateway_command(
                "set SQ610 HVAC mode",
                set_sq610_mode,
            )
            await self._async_request_debounced_refresh_after_sq610_write()
            return

        if self._is_fc600:
            device = self._device
            restore_preset = (
                device is not None and device.preset_mode == RAW_PRESET_OFF
            )
            raw_resume_preset = self._fc600_resume_raw_preset_mode

            async def set_fc600_mode() -> None:
                await self.coordinator.gateway.set_climate_device_mode(
                    self._device_id,
                    hvac_mode,
                )
                if restore_preset:
                    await self.coordinator.gateway.set_climate_device_preset(
                        self._device_id,
                        raw_resume_preset,
                    )

            await self._async_run_gateway_command(
                "set FC600 HVAC mode",
                set_fc600_mode,
            )
            await self.coordinator.async_request_debounced_refresh()
            return

        if not self._capabilities.uses_independent_preset_control:
            if hvac_mode == HVACMode.HEAT:
                await self._async_set_generic_raw_preset(RAW_PRESET_PERMANENT_HOLD)
                return
            if hvac_mode == HVACMode.COOL and not self._supports_cooling:
                return

        if not self._supports_cooling:
            return

        await self._async_run_gateway_command(
            "set HVAC mode",
            lambda: self.coordinator.gateway.set_climate_device_mode(
                self._device_id,
                hvac_mode,
            ),
        )
        await self.coordinator.async_request_debounced_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the exposed Salus hold mode."""
        if preset_mode == PRESET_STANDBY:
            if self._is_sq610:
                self._remember_current_sq610_preset()
                await self._async_set_sq610_raw_preset(RAW_PRESET_OFF)
                return
            if self._is_fc600:
                self._remember_current_fc600_preset()
                await self._async_set_fc600_raw_preset(RAW_PRESET_OFF)
                return
            raw_preset_mode = RAW_PRESET_OFF
        elif preset_mode == PRESET_PERMANENT_HOLD:
            if self._is_sq610:
                self._sq610_resume_preset_mode = PRESET_PERMANENT_HOLD
                await self._async_set_sq610_raw_preset(RAW_PRESET_PERMANENT_HOLD)
                return
            if self._is_fc600:
                self._fc600_resume_preset_mode = PRESET_PERMANENT_HOLD
                await self._async_set_fc600_raw_preset(RAW_PRESET_PERMANENT_HOLD)
                return
            raw_preset_mode = RAW_PRESET_PERMANENT_HOLD
        elif preset_mode == PRESET_FOLLOW_SCHEDULE:
            if self._is_sq610:
                self._sq610_resume_preset_mode = PRESET_FOLLOW_SCHEDULE
                await self._async_set_sq610_raw_preset(RAW_PRESET_FOLLOW_SCHEDULE)
                return
            if self._is_fc600:
                self._fc600_resume_preset_mode = PRESET_FOLLOW_SCHEDULE
                await self._async_set_fc600_raw_preset(RAW_PRESET_FOLLOW_SCHEDULE)
                return
            raw_preset_mode = RAW_PRESET_FOLLOW_SCHEDULE
        elif preset_mode == PRESET_ECO:
            if self._is_fc600:
                self._fc600_resume_preset_mode = PRESET_ECO
                await self._async_set_fc600_raw_preset(RAW_PRESET_ECO)
                return
            _LOGGER.warning(
                "Ignoring unsupported preset mode request for %s: %s",
                self._device_id,
                preset_mode,
            )
            return
        else:
            _LOGGER.warning(
                "Ignoring unsupported preset mode request for %s: %s",
                self._device_id,
                preset_mode,
            )
            return

        await self._async_run_gateway_command(
            "set preset",
            lambda: self.coordinator.gateway.set_climate_device_preset(
                self._device_id,
                raw_preset_mode,
            ),
        )
        await self.coordinator.async_request_debounced_refresh()

    async def async_turn_on(self) -> None:
        """Turn the thermostat on by resuming the previous active preset."""
        if self._is_sq610:
            self._remember_current_sq610_preset()
            await self._async_set_sq610_raw_preset(self._sq610_resume_raw_preset_mode)
            return
        if self._is_fc600:
            self._remember_current_fc600_preset()
            await self._async_set_fc600_raw_preset(self._fc600_resume_raw_preset_mode)
            return
        await self.async_set_preset_mode(PRESET_PERMANENT_HOLD)

    async def async_turn_off(self) -> None:
        """Turn the thermostat off by putting it in standby."""
        await self.async_set_preset_mode(PRESET_STANDBY)
