"""Support for Salus binary sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .coordinator import SalusData, SalusRuntimeData
from .entity import SalusEntity, async_add_salus_entities

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Salus binary sensors from a config entry."""
    runtime_data: SalusRuntimeData = config_entry.runtime_data
    coordinator = runtime_data.coordinator

    async_add_salus_entities(
        config_entry,
        coordinator,
        async_add_entities,
        lambda device_id: SalusBinarySensor(coordinator, device_id),
        lambda data: data.binary_sensor_devices,
    )


class SalusBinarySensor(SalusEntity, BinarySensorEntity):
    """Representation of a Salus binary sensor."""

    @property
    def _device(self) -> Any | None:
        """Return the current binary sensor snapshot."""
        data: SalusData | None = self.coordinator.data
        return None if data is None else data.binary_sensor_devices.get(self._device_id)

    @property
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        return None if self._device is None else self._device.is_on

    @property
    def device_class(self) -> str | None:
        """Return the device class of the binary sensor."""
        return None if self._device is None else self._device.device_class

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the entity category for diagnostic/config child sensors."""
        if self._device is None:
            return None
        if getattr(self._device, "entity_category", None) == "diagnostic":
            return EntityCategory.DIAGNOSTIC
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return diagnostic attributes supplied by the client."""
        if self._device is None:
            return None
        return getattr(self._device, "extra_state_attributes", None)
