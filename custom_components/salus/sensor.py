"""Support for Salus temperature sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SalusData, SalusRuntimeData
from .entity import SalusEntity, async_add_salus_entities

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Salus sensors from a config entry."""
    runtime_data: SalusRuntimeData = config_entry.runtime_data
    coordinator = runtime_data.coordinator

    async_add_salus_entities(
        config_entry,
        coordinator,
        async_add_entities,
        lambda device_id: SalusSensor(coordinator, device_id),
        lambda data: data.sensor_devices,
    )


class SalusSensor(SalusEntity, SensorEntity):
    """Representation of a Salus sensor."""

    @property
    def _device(self) -> Any | None:
        """Return the current sensor snapshot."""
        data: SalusData | None = self.coordinator.data
        return None if data is None else data.sensor_devices.get(self._device_id)

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return None if self._device is None else self._device.state

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of this entity, if any."""
        return None if self._device is None else self._device.unit_of_measurement

    @property
    def device_class(self) -> str | None:
        """Return the device class of the sensor."""
        return None if self._device is None else self._device.device_class
