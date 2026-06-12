"""Support for Salus thermostat child locks."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .coordinator import SalusConfigEntry
from .entity import SalusEntity, async_setup_salus_platform_entities

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SalusConfigEntry,
    async_add_entities,
) -> None:
    """Set up Salus thermostat lock entities from a config entry."""
    async_setup_salus_platform_entities(
        config_entry,
        async_add_entities,
        SalusThermostatLock,
        lambda data: {
            device_id: device
            for device_id, device in data.climate_devices.items()
            if getattr(device, "locked", None) is not None
        },
    )


class SalusThermostatLock(SalusEntity, LockEntity):
    """Representation of a Salus thermostat child lock."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "keypad_lock"
    _data_collection = "climate_devices"

    def __init__(self, coordinator, device_id: str) -> None:
        """Initialize the lock entity."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_lock"

    @property
    def is_locked(self) -> bool | None:
        """Return whether the thermostat keypad is locked."""
        if self._device is None:
            return None
        return self._pending_or_reported("is_locked", self._device.locked is True)

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the thermostat keypad."""
        await self._async_run_pending_gateway_command(
            "lock thermostat keypad",
            lambda: self.coordinator.gateway.set_climate_device_locked(
                self._device_id,
                True,
            ),
            {"is_locked": True},
        )

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the thermostat keypad."""
        await self._async_run_pending_gateway_command(
            "unlock thermostat keypad",
            lambda: self.coordinator.gateway.set_climate_device_locked(
                self._device_id,
                False,
            ),
            {"is_locked": False},
        )
