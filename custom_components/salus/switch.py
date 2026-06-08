"""Support for Salus switch devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant

from .coordinator import SalusConfigEntry
from .entity import SalusEntity, async_setup_salus_platform_entities

PARALLEL_UPDATES = 1

MULTIFUNCTION_SWITCH_MODELS = {"RS600", "SR600"}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SalusConfigEntry,
    async_add_entities,
) -> None:
    """Set up Salus switches from a config entry."""
    async_setup_salus_platform_entities(
        config_entry,
        async_add_entities,
        SalusSwitch,
        lambda data: data.switch_devices,
    )


class SalusSwitch(SalusEntity, SwitchEntity):
    """Representation of a Salus switch."""

    _attr_name = None
    _data_collection = "switch_devices"

    def _device_info_unique_id(self, device: Any) -> str:
        """Group RS600/SR600 relay endpoints under their physical device."""
        device_data = getattr(device, "data", None)
        if not isinstance(device_data, dict):
            return super()._device_info_unique_id(device)

        unique_id = device_data.get("UniID")
        if not isinstance(unique_id, str):
            return super()._device_info_unique_id(device)

        if getattr(device, "model", None) in MULTIFUNCTION_SWITCH_MODELS:
            return unique_id

        data = self.coordinator.data
        if data is not None and unique_id in data.cover_devices:
            return unique_id

        return super()._device_info_unique_id(device)

    @property
    def device_class(self) -> str | None:
        """Return the device class of the switch."""
        return self._device_attr("device_class")

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        return self._pending_or_reported("is_on", self._device_attr("is_on"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_run_pending_gateway_command(
            "turn on switch",
            lambda: self.coordinator.gateway.turn_on_switch_device(self._device_id),
            {"is_on": True},
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_run_pending_gateway_command(
            "turn off switch",
            lambda: self.coordinator.gateway.turn_off_switch_device(self._device_id),
            {"is_on": False},
        )
