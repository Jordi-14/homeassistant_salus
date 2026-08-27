"""Support for Salus switch devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant

from .coordinator import SalusConfigEntry, SalusData
from .entity import SalusEntity, async_setup_salus_platform_entities

PARALLEL_UPDATES = 1

MULTIFUNCTION_SWITCH_MODELS = {"RS600", "SR600"}


def switch_device_registry_unique_id(
    device: Any,
    data: SalusData | None,
) -> str | None:
    """Return the physical-device UniID a grouped switch endpoint uses.

    Returns None when the switch keeps its own unique_id as the
    device-registry identifier. Shared with async_remove_config_entry_device
    so the removal guard uses the same device identity as
    SalusSwitch.device_info.
    """
    device_data = getattr(device, "data", None)
    if not isinstance(device_data, dict):
        return None

    unique_id = device_data.get("UniID")
    if not isinstance(unique_id, str):
        return None

    if getattr(device, "model", None) in MULTIFUNCTION_SWITCH_MODELS:
        return unique_id

    if data is not None and unique_id in data.cover_devices:
        return unique_id

    return None


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
        unique_id = switch_device_registry_unique_id(device, self.coordinator.data)
        if unique_id is not None:
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
