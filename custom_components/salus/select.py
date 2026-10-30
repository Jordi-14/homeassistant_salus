"""Experimental floor-comfort control for client-verified thermostat profiles."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SalusConfigEntry, SalusDataUpdateCoordinator
from .entity import SalusEntity, async_setup_salus_platform_entities

PARALLEL_UPDATES = 1
_OPTIONS = ("off", "level_1", "level_2", "level_3")
PENDING_COMFORT_SECONDS = 120.0


async def async_setup_entry(
    hass: HomeAssistant, config_entry: SalusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_setup_salus_platform_entities(config_entry, async_add_entities,
        SalusComfortWarmFloorSelect,
        lambda data: {key: device for key, device in data.climate_devices.items()
                      if getattr(device, "supports_comfort_warm_floor", False)})


class SalusComfortWarmFloorSelect(SalusEntity, SelectEntity):
    """Keep gateway acknowledgement separate from confirmed device state."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "comfort_warm_floor"
    _attr_options = list(_OPTIONS)
    _data_collection = "climate_devices"

    def __init__(self, coordinator: SalusDataUpdateCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_comfort_warm_floor"

    @property
    def current_option(self) -> str | None:
        settings = self._device_attr("advanced_settings")
        level = getattr(settings, "comfort_warm_floor", None)
        reported = _OPTIONS[level] if type(level) is int and 0 <= level <= 3 else None
        return self._pending_or_reported("current_option", reported)

    @property
    def assumed_state(self) -> bool:
        # Standard HA attribute: consumers can wait for assumed_state to clear
        # rather than mistaking the optimistic pending level for confirmation.
        _ = self.current_option
        return "current_option" in self._pending_state

    @property
    def available(self) -> bool:
        return super().available and bool(self._device_attr("supports_comfort_warm_floor", False))

    async def async_select_option(self, option: str) -> None:
        if option not in _OPTIONS:
            raise ServiceValidationError("Unknown Comfort Warm Floor option")
        if not self.available:
            raise ServiceValidationError("Comfort Warm Floor control is unavailable")
        await self._async_run_pending_gateway_command(
            "set comfort warm floor",
            lambda: self.coordinator.gateway.set_climate_device_comfort_warm_floor(self._device_id, _OPTIONS.index(option)),
            {"current_option": option}, pending_timeout=PENDING_COMFORT_SECONDS,
        )
