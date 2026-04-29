"""Base entity helpers for the Salus iT600 integration.

This module provides the entity pattern for all Salus device platforms (climate,
switch, binary_sensor, etc.). All entities extend SalusEntity and automatically
receive coordinator updates through the CoordinatorEntity mixin.

Entity Lifecycle:
    1. Platform's async_setup_entry() calls async_add_salus_entities()
    2. Entity factory creates SalusEntity subclass instances for each device
    3. Each entity subscribes to coordinator.async_add_listener()
    4. Whenever coordinator.data updates, all entities' _handle_coordinator_update() fires
    5. Entity properties read from coordinator.data[device_id] to populate UI

Device Info Pattern:
    Each entity provides device_info to group entities by device in Home Assistant.
    Devices are identified by (DOMAIN, unique_id) tuple. If device is not the gateway
    itself, it includes via_device=(DOMAIN, gateway_id) to show gateway as parent.

Availability:
    Entities are available if:
    - Coordinator has recent data (not unavailable)
    - Device exists in latest data snapshot
    - Device.available property is True (device online at gateway)

Extending for New Platforms:
    1. Create platform module (e.g., light.py)
    2. Extend SalusEntity with platform-specific methods:
       - _device property (returns current device from coordinator.data)
       - async_turn_on/off, set_brightness, etc. (call gateway methods)
    3. Override async_update_data callback as needed
    4. In async_setup_entry(), use async_add_salus_entities() helper
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from salus_it600.exceptions import IT600CommandError, IT600ConnectionError

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
        """Return the current Salus device snapshot."""
        raise NotImplementedError

    async def _async_run_gateway_command(
        self,
        action: str,
        command: Callable[[], Awaitable[None]],
    ) -> None:
        """Run one gateway command and convert client failures to HA service errors."""
        try:
            async with self.coordinator.gateway_lock:
                await command()
        except (IT600CommandError, IT600ConnectionError) as ex:
            raise HomeAssistantError(
                f"Failed to {action} for Salus device {self._device_id}: {ex}"
            ) from ex

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self._device
        return (
            super().available
            and device is not None
            and bool(getattr(device, "available", True))
        )

    def _device_info_unique_id(self, device: Any) -> str:
        """Return the device-registry identifier for a primary entity."""
        return getattr(device, "unique_id", self._device_id)

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return the device info."""
        device = self._device
        if device is None:
            return None

        parent_unique_id = getattr(device, "parent_unique_id", None)
        if parent_unique_id:
            return {"identifiers": {(DOMAIN, parent_unique_id)}}

        unique_id = self._device_info_unique_id(device)
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
    """Add existing and newly discovered Salus entities for one platform.

    Reusable helper for all platform setup functions. Handles:
    - Creating entities for devices already known at setup
    - Listening for coordinator updates and creating entities for newly discovered devices
    - Preventing duplicate entity creation

    Usage in a platform (e.g., switch.py):
        async def async_setup_entry(hass, config_entry, async_add_entities):
            coordinator = config_entry.runtime_data.coordinator
            async_add_salus_entities(
                config_entry,
                coordinator,
                async_add_entities,
                entity_factory=lambda device_id: SalusSwitch(coordinator, device_id),
                devices_getter=lambda data: data.switch_devices,
            )

    Args:
        config_entry: Home Assistant config entry (used for unload cleanup)
        coordinator: Data coordinator with device snapshots
        async_add_entities: Home Assistant callback to add entities to platform
        entity_factory: Callable(device_id) → SalusEntity subclass instance
        devices_getter: Callable(SalusData) → dict of devices for this platform
    """
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
        async_add_entities(
            [entity_factory(device_id) for device_id in sorted(new_device_ids)]
        )

    _async_add_new_entities()
    config_entry.async_on_unload(
        coordinator.async_add_listener(_async_add_new_entities)
    )
