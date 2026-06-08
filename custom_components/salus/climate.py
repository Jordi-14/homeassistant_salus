"""Support for Salus climate devices."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant, callback
from salus_it600.const import HoldType
from salus_it600.device_models import (
    SQ610_HOLD_AUTO,
    SQ610_HOLD_PERMANENT,
    SQ610_HOLD_STANDBY,
    SQ610_HOLD_AWAY,
    SQ610_MODE_COOL,
    SQ610_RUNNING_COOL,
    is_fan_coil_model,
)

from ._climate_state import (
    HA_TO_RAW_FAN_MODE,
    PRESET_ECO,
    PRESET_FOLLOW_SCHEDULE,
    PRESET_PERMANENT_HOLD,
    PRESET_STANDBY,
    PRESET_AWAY,
    PRESET_SCHEDULE_OVERRIDE,
    RAW_PRESET_ECO,
    RAW_PRESET_FOLLOW_SCHEDULE,
    RAW_PRESET_OFF,
    RAW_PRESET_PERMANENT_HOLD,
    RAW_PRESET_SCHEDULE_OVERRIDE,
    RAW_PRESET_AWAY,
    ClimateCapabilities,
    ClimateViewState,
    build_climate_capabilities,
    build_climate_view_state,
)
from .coordinator import SalusConfigEntry, is_sq610_device
from .entity import SalusEntity, async_setup_salus_platform_entities

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1
TARGET_TEMPERATURE_DEBOUNCE_SECONDS = 0.3
PENDING_TARGET_TEMPERATURE_TIMEOUT_SECONDS = 30.0
TARGET_TEMPERATURE_CONFIRMATION_EPSILON = 0.01

SQ610_RESUME_PRESET_TO_RAW = {
    PRESET_FOLLOW_SCHEDULE: RAW_PRESET_FOLLOW_SCHEDULE,
    PRESET_PERMANENT_HOLD: RAW_PRESET_PERMANENT_HOLD,
    PRESET_AWAY: RAW_PRESET_AWAY,
}
FC600_RESUME_PRESET_TO_RAW = {
    PRESET_FOLLOW_SCHEDULE: RAW_PRESET_FOLLOW_SCHEDULE,
    PRESET_PERMANENT_HOLD: RAW_PRESET_PERMANENT_HOLD,
    PRESET_ECO: RAW_PRESET_ECO,
}
SQ610_HOLD_TO_PRESET = {
    SQ610_HOLD_AUTO: PRESET_FOLLOW_SCHEDULE,
    SQ610_HOLD_PERMANENT: PRESET_PERMANENT_HOLD,
    SQ610_HOLD_AWAY: PRESET_AWAY,
    HoldType.TEMPORARY_HOLD: PRESET_SCHEDULE_OVERRIDE,
    SQ610_HOLD_STANDBY: None,
}
SQ610_RAW_PRESET_TO_PRESET = {
    RAW_PRESET_FOLLOW_SCHEDULE: PRESET_FOLLOW_SCHEDULE,
    RAW_PRESET_PERMANENT_HOLD: PRESET_PERMANENT_HOLD,
    RAW_PRESET_AWAY: PRESET_AWAY,
    RAW_PRESET_SCHEDULE_OVERRIDE: PRESET_SCHEDULE_OVERRIDE,
}
FC600_RAW_PRESET_TO_PRESET = {
    RAW_PRESET_FOLLOW_SCHEDULE: PRESET_FOLLOW_SCHEDULE,
    RAW_PRESET_ECO: PRESET_ECO,
    RAW_PRESET_PERMANENT_HOLD: PRESET_PERMANENT_HOLD,
    RAW_PRESET_SCHEDULE_OVERRIDE: PRESET_SCHEDULE_OVERRIDE,
}
EXPOSED_PRESET_TO_RAW = {
    PRESET_STANDBY: RAW_PRESET_OFF,
    PRESET_PERMANENT_HOLD: RAW_PRESET_PERMANENT_HOLD,
    PRESET_FOLLOW_SCHEDULE: RAW_PRESET_FOLLOW_SCHEDULE,
    PRESET_ECO: RAW_PRESET_ECO,
    PRESET_AWAY: RAW_PRESET_AWAY,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SalusConfigEntry,
    async_add_entities,
) -> None:
    """Set up Salus thermostats from a config entry."""
    async_setup_salus_platform_entities(
        config_entry,
        async_add_entities,
        SalusThermostat,
        lambda data: data.climate_devices,
    )


class SalusThermostat(SalusEntity, ClimateEntity):
    """Representation of a Salus thermostat."""

    _enable_turn_on_off_backwards_compatibility = False
    _attr_name = None
    _attr_translation_key = "thermostat"
    _data_collection = "climate_devices"

    def __init__(self, coordinator: Any, device_id: str) -> None:
        """Initialize a Salus thermostat entity."""
        super().__init__(coordinator, device_id)
        self._sq610_resume_preset_mode: str | None = None
        self._sq610_supports_cooling = False
        self._sq610_logged_unknown_hold_types: set[str] = set()
        self._fc600_resume_preset_mode: str | None = None
        self._pending_target_temperature: float | None = None
        self._pending_target_temperature_expires_at: float | None = None
        self._target_temperature_request_id = 0

    @property
    def _is_sq610(self) -> bool:
        """Return whether the thermostat is a Quantum model."""
        return is_sq610_device(self._device)

    @property
    def _is_fc600(self) -> bool:
        """Return whether the thermostat is an FC600-family fan coil."""
        device = self._device
        return is_fan_coil_model(getattr(device, "model", None))

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
            sq610_resume_preset_mode=resume_preset_mode,
            sq610_known_supports_cooling=known_supports_cooling,
            fc600_resume_preset_mode=fc600_resume_preset_mode,
        )

    @property
    def _capabilities(self) -> ClimateCapabilities:
        """Return the current Salus control capabilities for this device."""
        return build_climate_capabilities(
            self._device,
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
        return self._device_attr("temperature_unit")

    @property
    def precision(self) -> float | None:
        """Return the precision of the system."""
        return self._device_attr("precision")

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
        if (pending := self._fresh_pending_target_temperature()) is not None:
            return pending
        return self._view.target_temperature

    @property
    def max_temp(self) -> float | None:
        """Return the maximum target temperature."""
        return self._device_attr("max_temp")

    @property
    def min_temp(self) -> float | None:
        """Return the minimum target temperature."""
        return self._device_attr("min_temp")

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
        return self._device_attr("locked")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose normalized Salus state while the HA controls stay simplified."""
        device = self._device
        if device is None:
            return {}

        attributes = {
            "salus_hvac_mode": device.hvac_mode,
            "salus_preset_mode": device.preset_mode,
            "salus_hold_type": getattr(device, "hold_type", None),
            "salus_system_mode": getattr(device, "system_mode", None),
            "salus_running_state": getattr(device, "running_state", None),
            "salus_heating_setpoint": getattr(device, "heating_setpoint", None),
            "salus_cooling_setpoint": getattr(device, "cooling_setpoint", None),
            "salus_cooling_capability_source": getattr(
                device,
                "cooling_capability_source",
                None,
            ),
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
        """Return the active non-standby SQ610 preset from normalized state."""
        device = self._device
        if device is None:
            return None

        hold_type = getattr(device, "hold_type", None)
        if hold_type in SQ610_HOLD_TO_PRESET:
            return SQ610_HOLD_TO_PRESET[hold_type]
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

        return SQ610_RAW_PRESET_TO_PRESET.get(getattr(device, "preset_mode", None))

    def _remember_current_sq610_preset(self) -> None:
        """Remember the last active hold/schedule preset for standby resume."""
        preset_mode = self._current_sq610_preset_mode()
        if preset_mode is not None and preset_mode in SQ610_RESUME_PRESET_TO_RAW:
            self._sq610_resume_preset_mode = preset_mode

    def _current_fc600_preset_mode(self) -> str | None:
        """Return the active non-off FC600 preset from parsed state."""
        return FC600_RAW_PRESET_TO_PRESET.get(self._device_attr("preset_mode"))

    def _remember_current_fc600_preset(self) -> None:
        """Remember the last active FC600 preset for off-state resume."""
        preset_mode = self._current_fc600_preset_mode()
        if preset_mode is not None and preset_mode in FC600_RESUME_PRESET_TO_RAW:
            self._fc600_resume_preset_mode = preset_mode

    def _remember_current_family_preset(self) -> None:
        """Remember the active preset for device families with off/standby resume."""
        if self._is_sq610:
            self._remember_current_sq610_preset()
        elif self._is_fc600:
            self._remember_current_fc600_preset()

    def _remember_requested_resume_preset(self, preset_mode: str) -> None:
        """Remember an explicitly selected preset for later off/standby resume."""
        if self._is_sq610 and preset_mode in SQ610_RESUME_PRESET_TO_RAW:
            self._sq610_resume_preset_mode = preset_mode
        elif self._is_fc600 and preset_mode in FC600_RESUME_PRESET_TO_RAW:
            self._fc600_resume_preset_mode = preset_mode

    def _sq610_snapshot_supports_cooling(self) -> bool:
        """Return whether the current SQ610 snapshot proves cooling support."""
        device = self._device
        return bool(
            device is not None
            and (
                getattr(device, "supports_cooling", False)
                or HVACMode.COOL in (getattr(device, "hvac_modes", None) or [])
                or getattr(device, "system_mode", None) == SQ610_MODE_COOL
                or getattr(device, "running_state", None) == SQ610_RUNNING_COOL
            )
        )

    def _remember_sq610_cooling_support(self) -> None:
        """Keep Cool exposed after an SQ610 has proved cooling support once."""
        if self._sq610_snapshot_supports_cooling():
            self._sq610_supports_cooling = True

    def _loop_time(self) -> float:
        """Return the event-loop monotonic time."""
        loop = getattr(getattr(self, "hass", None), "loop", None)
        if loop is not None:
            return loop.time()
        return asyncio.get_running_loop().time()

    def _set_pending_target_temperature(self, temperature: float) -> int:
        """Store a Home Assistant-facing target temperature while it is pending."""
        self._target_temperature_request_id += 1
        self._pending_target_temperature = temperature
        self._pending_target_temperature_expires_at = (
            self._loop_time() + PENDING_TARGET_TEMPERATURE_TIMEOUT_SECONDS
        )
        self._async_write_state_if_added()
        return self._target_temperature_request_id

    def _clear_pending_target_temperature(self, request_id: int | None = None) -> None:
        """Clear a pending target temperature request."""
        if request_id is not None and request_id != self._target_temperature_request_id:
            return
        self._pending_target_temperature = None
        self._pending_target_temperature_expires_at = None

    def _fresh_pending_target_temperature(self) -> float | None:
        """Return a pending target temperature unless it timed out."""
        temperature = self._pending_target_temperature
        if temperature is None:
            return None

        expires_at = self._pending_target_temperature_expires_at
        if expires_at is not None and self._loop_time() >= expires_at:
            self._clear_pending_target_temperature()
            return None

        return temperature

    def _pending_target_temperature_is_confirmed(self) -> bool:
        """Return whether the current gateway snapshot confirms the pending target."""
        pending = self._pending_target_temperature
        reported = self._view.target_temperature
        return (
            pending is not None
            and reported is not None
            and abs(reported - pending) <= TARGET_TEMPERATURE_CONFIRMATION_EPSILON
        )

    def _clear_confirmed_pending_target_temperature(self) -> bool:
        """Clear a pending target temperature once the gateway reports it."""
        if not self._pending_target_temperature_is_confirmed():
            return False
        self._clear_pending_target_temperature()
        return True

    def _async_write_state_if_added(self) -> None:
        """Write state only once Home Assistant has registered the entity."""
        if getattr(self, "hass", None) is None or self.entity_id is None:
            return
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._clear_confirmed_pending_target_temperature()
        super()._handle_coordinator_update()

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

    async def _async_request_climate_command_refresh(self, is_sq610: bool) -> None:
        """Request the correct post-command refresh for this climate family."""
        if is_sq610:
            await self._async_request_debounced_refresh_after_sq610_write()
        else:
            await self.coordinator.async_request_debounced_refresh()

    async def _async_set_raw_preset(self, raw_preset_mode: str) -> None:
        """Set a Salus hold/preset value and refresh state."""
        is_sq610 = self._is_sq610
        action = (
            "set SQ610 preset"
            if is_sq610
            else "set FC600 preset"
            if self._is_fc600
            else "set preset"
        )
        await self._async_run_gateway_command(
            action,
            lambda: self.coordinator.gateway.set_climate_device_preset(
                self._device_id,
                raw_preset_mode,
            ),
        )
        await self._async_request_climate_command_refresh(is_sq610)

    async def _async_set_hvac_mode_and_restore_preset(
        self,
        action: str,
        hvac_mode: HVACMode,
        *,
        restore_preset: bool,
        raw_resume_preset: str,
        is_sq610: bool,
    ) -> None:
        """Set HVAC mode and restore a remembered preset when leaving off state."""

        async def set_mode() -> None:
            await self.coordinator.gateway.set_climate_device_mode(
                self._device_id,
                hvac_mode,
            )
            if restore_preset:
                await self.coordinator.gateway.set_climate_device_preset(
                    self._device_id,
                    raw_resume_preset,
                )

        await self._async_run_gateway_command(action, set_mode)
        await self._async_request_climate_command_refresh(is_sq610)

    async def _async_set_debounced_target_temperature(
        self,
        temperature: float,
        *,
        action: str,
        is_sq610: bool,
    ) -> None:
        """Debounce target temperature writes while exposing the desired value."""
        request_id = self._set_pending_target_temperature(temperature)
        await asyncio.sleep(TARGET_TEMPERATURE_DEBOUNCE_SECONDS)

        if request_id != self._target_temperature_request_id:
            return

        try:
            await self._async_run_gateway_command(
                action,
                lambda: self.coordinator.gateway.set_climate_device_temperature(
                    self._device_id,
                    temperature,
                ),
            )
        except Exception:
            self._clear_pending_target_temperature(request_id)
            self._async_write_state_if_added()
            raise

        await self._async_request_climate_command_refresh(is_sq610)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        temperature = float(temperature)

        if self._is_sq610:
            if getattr(self._device, "hold_type", None) == SQ610_HOLD_STANDBY:
                _LOGGER.debug(
                    "Ignoring SQ610 target temperature change while %s is in standby",
                    self._device_id,
                )
                return
            await self._async_set_debounced_target_temperature(
                temperature,
                action="set SQ610 target temperature",
                is_sq610=True,
            )
            return

        if self._is_fc600 and self._device_attr("preset_mode") in {
            RAW_PRESET_OFF,
            RAW_PRESET_ECO,
        }:
            _LOGGER.debug(
                "Ignoring FC600 target temperature change while %s is in %s",
                self._device_id,
                self._device_attr("preset_mode"),
            )
            return

        await self._async_set_debounced_target_temperature(
            temperature,
            action="set target temperature",
            is_sq610=False,
        )

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

        await self._async_run_gateway_command_and_refresh(
            "set fan mode",
            lambda: self.coordinator.gateway.set_climate_device_fan_mode(
                self._device_id,
                mode,
            ),
        )

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
            self._remember_current_family_preset()
            await self._async_set_raw_preset(RAW_PRESET_OFF)
            return
        if hvac_mode == HVACMode.AUTO:
            await self._async_set_raw_preset(RAW_PRESET_FOLLOW_SCHEDULE)
            return

        if self._is_sq610:
            await self._async_set_hvac_mode_and_restore_preset(
                "set SQ610 HVAC mode",
                hvac_mode,
                restore_preset=self._device_attr("hold_type") == SQ610_HOLD_STANDBY,
                raw_resume_preset=self._sq610_resume_raw_preset_mode,
                is_sq610=True,
            )
            return

        if self._is_fc600:
            await self._async_set_hvac_mode_and_restore_preset(
                "set FC600 HVAC mode",
                hvac_mode,
                restore_preset=self._device_attr("preset_mode") == RAW_PRESET_OFF,
                raw_resume_preset=self._fc600_resume_raw_preset_mode,
                is_sq610=False,
            )
            return

        if not self._capabilities.uses_independent_preset_control:
            if hvac_mode == HVACMode.HEAT:
                await self._async_set_raw_preset(RAW_PRESET_PERMANENT_HOLD)
                return
            if hvac_mode == HVACMode.COOL and not self._supports_cooling:
                return

        if not self._supports_cooling:
            return

        await self._async_run_gateway_command_and_refresh(
            "set HVAC mode",
            lambda: self.coordinator.gateway.set_climate_device_mode(
                self._device_id,
                hvac_mode,
            ),
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the exposed Salus hold mode."""
        if preset_mode != PRESET_STANDBY and preset_mode not in self.preset_modes:
            _LOGGER.warning(
                "Ignoring unsupported preset mode request for %s: %s",
                self._device_id,
                preset_mode,
            )
            return

        if preset_mode == PRESET_SCHEDULE_OVERRIDE:
            return

        raw_preset_mode = EXPOSED_PRESET_TO_RAW.get(preset_mode)
        if raw_preset_mode is None:
            _LOGGER.warning(
                "Ignoring unsupported preset mode request for %s: %s",
                self._device_id,
                preset_mode,
            )
            return

        if preset_mode == PRESET_STANDBY:
            self._remember_current_family_preset()
        else:
            self._remember_requested_resume_preset(preset_mode)
        await self._async_set_raw_preset(raw_preset_mode)

    async def async_turn_on(self) -> None:
        """Turn the thermostat on by resuming the previous active preset."""
        if self._is_sq610:
            self._remember_current_family_preset()
            await self._async_set_raw_preset(self._sq610_resume_raw_preset_mode)
            return
        if self._is_fc600:
            self._remember_current_family_preset()
            await self._async_set_raw_preset(self._fc600_resume_raw_preset_mode)
            return
        await self._async_set_raw_preset(RAW_PRESET_PERMANENT_HOLD)

    async def async_turn_off(self) -> None:
        """Turn the thermostat off by putting it in standby."""
        await self.async_set_preset_mode(PRESET_STANDBY)
