"""Support for Salus cover devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import ATTR_POSITION, CoverEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SalusData, SalusRuntimeData
from .entity import SalusEntity, async_add_salus_entities

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Salus cover devices from a config entry."""
    runtime_data: SalusRuntimeData = config_entry.runtime_data
    coordinator = runtime_data.coordinator

    async_add_salus_entities(
        config_entry,
        coordinator,
        async_add_entities,
        lambda device_id: SalusCover(coordinator, device_id),
        lambda data: data.cover_devices,
    )


class SalusCover(SalusEntity, CoverEntity):
    """Representation of a Salus cover."""

    @property
    def _device(self) -> Any | None:
        """Return the current cover snapshot."""
        data: SalusData | None = self.coordinator.data
        return None if data is None else data.cover_devices.get(self._device_id)

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return 0 if self._device is None else self._device.supported_features

    @property
    def device_class(self) -> str | None:
        """Return the device class of the cover."""
        return None if self._device is None else self._device.device_class

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of the cover."""
        return None if self._device is None else self._device.current_cover_position

    @property
    def is_opening(self) -> bool | None:
        """Return if the cover is opening."""
        return None if self._device is None else self._device.is_opening

    @property
    def is_closing(self) -> bool | None:
        """Return if the cover is closing."""
        return None if self._device is None else self._device.is_closing

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        return None if self._device is None else self._device.is_closed

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._async_run_gateway_command(
            "open cover",
            lambda: self.coordinator.gateway.open_cover(self._device_id),
        )
        await self.coordinator.async_request_debounced_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self._async_run_gateway_command(
            "close cover",
            lambda: self.coordinator.gateway.close_cover(self._device_id),
        )
        await self.coordinator.async_request_debounced_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        if position is None:
            return

        await self._async_run_gateway_command(
            "set cover position",
            lambda: self.coordinator.gateway.set_cover_position(
                self._device_id,
                position,
            ),
        )
        await self.coordinator.async_request_debounced_refresh()
