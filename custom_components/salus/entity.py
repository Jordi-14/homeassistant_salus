"""Base entity helpers for the Salus iT600 integration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SalusData, SalusDataUpdateCoordinator


class SalusEntity(CoordinatorEntity[SalusDataUpdateCoordinator]):
    """Base class for Salus entities."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: SalusDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = device_id

    @property
    def _device(self) -> Any | None:
        """Return the current pyit600 device snapshot."""
        raise NotImplementedError

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self._device
        return (
            super().available
            and device is not None
            and bool(getattr(device, "available", True))
        )

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return the device info."""
        device = self._device
        if device is None:
            return None

        unique_id = getattr(device, "unique_id", self._device_id)
        device_info: DeviceInfo = {
            "identifiers": {(DOMAIN, unique_id)},
            "name": getattr(device, "name", unique_id),
            "manufacturer": getattr(device, "manufacturer", "SALUS"),
            "model": getattr(device, "model", None),
            "sw_version": getattr(device, "sw_version", None),
        }

        if self.coordinator.gateway_id and self.coordinator.gateway_id != unique_id:
            device_info["via_device"] = (DOMAIN, self.coordinator.gateway_id)

        return device_info


def async_add_salus_entities(
    config_entry: ConfigEntry,
    coordinator: SalusDataUpdateCoordinator,
    async_add_entities: Callable[[list[SalusEntity]], None],
    entity_factory: Callable[[str], SalusEntity],
    devices_getter: Callable[[SalusData], Mapping[str, Any]],
) -> None:
    """Add existing and newly discovered Salus entities for one platform."""
    known_devices: set[str] = set()

    @callback
    def _async_add_new_entities() -> None:
        if coordinator.data is None:
            return

        current_devices = set(devices_getter(coordinator.data))
        new_device_ids = current_devices - known_devices
        if not new_device_ids:
            return

        known_devices.update(new_device_ids)
        async_add_entities([entity_factory(device_id) for device_id in sorted(new_device_ids)])

    _async_add_new_entities()
    config_entry.async_on_unload(coordinator.async_add_listener(_async_add_new_entities))
