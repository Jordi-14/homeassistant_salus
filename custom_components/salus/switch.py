"""Support for Salus switch devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SalusData, SalusRuntimeData
from .entity import SalusEntity, async_add_salus_entities

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Salus switches from a config entry."""
    runtime_data: SalusRuntimeData = config_entry.runtime_data
    coordinator = runtime_data.coordinator

    async_add_salus_entities(
        config_entry,
        coordinator,
        async_add_entities,
        lambda device_id: SalusSwitch(coordinator, device_id),
        lambda data: data.switch_devices,
    )


class SalusSwitch(SalusEntity, SwitchEntity):
    """Representation of a Salus switch."""

    @property
    def _device(self) -> Any | None:
        """Return the current switch snapshot."""
        data: SalusData | None = self.coordinator.data
        return None if data is None else data.switch_devices.get(self._device_id)

    @property
    def device_class(self) -> str | None:
        """Return the device class of the switch."""
        return None if self._device is None else self._device.device_class

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        return None if self._device is None else self._device.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        async with self.coordinator.gateway_lock:
            await self.coordinator.gateway.turn_on_switch_device(self._device_id)
        await self.coordinator.async_request_debounced_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        async with self.coordinator.gateway_lock:
            await self.coordinator.gateway.turn_off_switch_device(self._device_id)
        await self.coordinator.async_request_debounced_refresh()
