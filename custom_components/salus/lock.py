"""Support for Salus thermostat child locks."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .coordinator import SalusData, SalusRuntimeData
from .entity import SalusEntity, async_add_salus_entities

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Salus thermostat lock entities from a config entry."""
    runtime_data: SalusRuntimeData = config_entry.runtime_data
    coordinator = runtime_data.coordinator

    async_add_salus_entities(
        config_entry,
        coordinator,
        async_add_entities,
        lambda device_id: SalusThermostatLock(coordinator, device_id),
        lambda data: {
            device_id: device
            for device_id, device in data.climate_devices.items()
            if getattr(device, "locked", None) is not None
        },
    )


class SalusThermostatLock(SalusEntity, LockEntity):
    """Representation of a Salus thermostat child lock."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, device_id: str) -> None:
        """Initialize the lock entity."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_lock"

    @property
    def _device(self) -> Any | None:
        """Return the current lockable thermostat snapshot."""
        data: SalusData | None = self.coordinator.data
        return None if data is None else data.climate_devices.get(self._device_id)

    @property
    def is_locked(self) -> bool | None:
        """Return whether the thermostat keypad is locked."""
        if self._device is None:
            return None
        return self._device.locked is True

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the thermostat keypad."""
        await self._async_run_gateway_command(
            "lock thermostat keypad",
            lambda: self.coordinator.gateway.set_climate_device_locked(
                self._device_id,
                True,
            ),
        )
        await self.coordinator.async_request_debounced_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the thermostat keypad."""
        await self._async_run_gateway_command(
            "unlock thermostat keypad",
            lambda: self.coordinator.gateway.set_climate_device_locked(
                self._device_id,
                False,
            ),
        )
        await self.coordinator.async_request_debounced_refresh()
