"""Support for Salus binary sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SalusConfigEntry, SalusDataUpdateCoordinator
from .entity import SalusEntity, async_setup_salus_platform_entities

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SalusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Salus binary sensors from a config entry."""
    async_setup_salus_platform_entities(
        config_entry,
        async_add_entities,
        SalusBinarySensor,
        lambda data: data.binary_sensor_devices,
    )


class SalusBinarySensor(SalusEntity, BinarySensorEntity):
    """Representation of a Salus binary sensor."""

    _data_collection = "binary_sensor_devices"

    def __init__(self, coordinator: SalusDataUpdateCoordinator, device_id: str) -> None:
        """Initialize a Salus binary sensor entity."""
        super().__init__(coordinator, device_id)
        self._set_child_entity_name_metadata(self._device)

    @property
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        return self._device_attr("is_on")

    @property
    def device_class(self) -> str | None:
        """Return the device class of the binary sensor."""
        return self._device_attr("device_class")

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
        return self._device_attr("extra_state_attributes")
