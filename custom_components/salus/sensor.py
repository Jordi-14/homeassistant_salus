"""Support for Salus temperature sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .coordinator import SalusConfigEntry
from .entity import SalusEntity, async_setup_salus_platform_entities

PARALLEL_UPDATES = 0

STATE_CLASS_BY_DEVICE_CLASS = {
    "battery": SensorStateClass.MEASUREMENT,
    "humidity": SensorStateClass.MEASUREMENT,
    "power": SensorStateClass.MEASUREMENT,
    "temperature": SensorStateClass.MEASUREMENT,
    "energy": SensorStateClass.TOTAL_INCREASING,
}


def sensor_device_registry_unique_id(device: Any) -> str | None:
    """Return the physical-device UniID a standalone sensor groups under.

    Returns None when the snapshot carries no usable UniID, in which case the
    sensor falls back to its own unique_id as the device-registry identifier.
    Shared with async_remove_config_entry_device so the removal guard uses the
    same device identity as SalusSensor.device_info.
    """
    device_data = getattr(device, "data", None)
    if isinstance(device_data, dict):
        unique_id = device_data.get("UniID")
        if isinstance(unique_id, str):
            return unique_id
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SalusConfigEntry,
    async_add_entities,
) -> None:
    """Set up Salus sensors from a config entry."""
    async_setup_salus_platform_entities(
        config_entry,
        async_add_entities,
        SalusSensor,
        lambda data: data.sensor_devices,
    )


class SalusSensor(SalusEntity, SensorEntity):
    """Representation of a Salus sensor."""

    _data_collection = "sensor_devices"

    def __init__(self, coordinator, device_id: str) -> None:
        """Initialize a Salus sensor entity."""
        super().__init__(coordinator, device_id)
        self._set_child_entity_name_metadata(self._device)

    def _device_info_unique_id(self, device: Any) -> str:
        """Group primary standalone sensors under their physical Salus device."""
        unique_id = sensor_device_registry_unique_id(device)
        if unique_id is not None:
            return unique_id
        return super()._device_info_unique_id(device)

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self._device_attr("state")

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of this entity, if any."""
        return self._device_attr("unit_of_measurement")

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the long-term statistics behavior for numeric sensors."""
        if self._device is None:
            return None
        return STATE_CLASS_BY_DEVICE_CLASS.get(self._device.device_class)

    @property
    def device_class(self) -> str | None:
        """Return the device class of the sensor."""
        return self._device_attr("device_class")

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the entity category for diagnostic/config child sensors."""
        if self._device is None:
            return None
        if getattr(self._device, "entity_category", None) == "diagnostic":
            return EntityCategory.DIAGNOSTIC
        return None
