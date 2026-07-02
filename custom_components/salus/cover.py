"""Support for Salus cover devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import ATTR_POSITION, CoverEntity
from homeassistant.core import HomeAssistant

from .const import COVER_POSITION_DEBOUNCE_SECONDS
from .coordinator import SalusConfigEntry
from .entity import SalusEntity, async_setup_salus_platform_entities

PARALLEL_UPDATES = 1

COVER_DEVICE_CLASS_BY_MODEL = {
    "RS600": "shutter",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SalusConfigEntry,
    async_add_entities,
) -> None:
    """Set up Salus cover devices from a config entry."""
    async_setup_salus_platform_entities(
        config_entry,
        async_add_entities,
        SalusCover,
        lambda data: data.cover_devices,
    )


class SalusCover(SalusEntity, CoverEntity):
    """Representation of a Salus cover."""

    _attr_name = None
    _data_collection = "cover_devices"

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return self._device_attr("supported_features", 0)

    @property
    def device_class(self) -> str | None:
        """Return the device class of the cover."""
        if self._device is None:
            return None
        return self._device.device_class or COVER_DEVICE_CLASS_BY_MODEL.get(
            self._device.model
        )

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of the cover."""
        return self._pending_or_reported(
            "current_cover_position",
            self._device_attr("current_cover_position"),
        )

    @property
    def is_opening(self) -> bool | None:
        """Return if the cover is opening."""
        return self._device_attr("is_opening")

    @property
    def is_closing(self) -> bool | None:
        """Return if the cover is closing."""
        return self._device_attr("is_closing")

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        return self._pending_or_reported("is_closed", self._device_attr("is_closed"))

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._async_run_pending_gateway_command(
            "open cover",
            lambda: self.coordinator.gateway.open_cover(self._device_id),
            {"current_cover_position": 100, "is_closed": False},
        )

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self._async_run_pending_gateway_command(
            "close cover",
            lambda: self.coordinator.gateway.close_cover(self._device_id),
            {"current_cover_position": 0, "is_closed": True},
        )

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        if position is None:
            return

        position = int(position)
        await self._async_run_pending_gateway_command(
            "set cover position",
            lambda: self.coordinator.gateway.set_cover_position(
                self._device_id,
                position,
            ),
            {"current_cover_position": position, "is_closed": position == 0},
            debounce_seconds=COVER_POSITION_DEBOUNCE_SECONDS,
        )
