"""Support for Salus it600MINITRV mode selection."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from salus_it600.const import MiniTrvMode
from salus_it600.device_models import MODEL_MINI_TRV

from .coordinator import SalusConfigEntry, SalusDataUpdateCoordinator
from .entity import SalusEntity, async_setup_salus_platform_entities

PARALLEL_UPDATES = 1

TRV_MODE_AUTO = "auto"
TRV_MODE_MANUAL_ON = "manual_on"
TRV_MODE_MANUAL_OFF = "manual_off"

OPTION_TO_TRV_MODE = {
    TRV_MODE_AUTO: MiniTrvMode.AUTO,
    TRV_MODE_MANUAL_ON: MiniTrvMode.MANUAL_ON,
    TRV_MODE_MANUAL_OFF: MiniTrvMode.MANUAL_OFF,
}
TRV_MODE_TO_OPTION = {mode: option for option, mode in OPTION_TO_TRV_MODE.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SalusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Salus TRV mode selects from a config entry."""
    async_setup_salus_platform_entities(
        config_entry,
        async_add_entities,
        SalusMiniTrvModeSelect,
        lambda data: {
            device_id: device
            for device_id, device in data.binary_sensor_devices.items()
            if getattr(device, "model", None) == MODEL_MINI_TRV
            and getattr(device, "mini_trv_mode", None) is not None
        },
    )


class SalusMiniTrvModeSelect(SalusEntity, SelectEntity):
    """Auto / Manual On (valve open) / Manual Off (valve closed) for a MiniTRV."""

    _attr_translation_key = "trv_mode"
    _attr_options = list(OPTION_TO_TRV_MODE)
    _data_collection = "binary_sensor_devices"

    def __init__(self, coordinator: SalusDataUpdateCoordinator, device_id: str) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_mode"

    @property
    def current_option(self) -> str | None:
        """Return the selected mode, or None for modes the TRV enters itself."""
        reported = TRV_MODE_TO_OPTION.get(self._device_attr("mini_trv_mode"))
        return self._pending_or_reported("current_option", reported)

    async def async_select_option(self, option: str) -> None:
        """Switch the TRV to the selected mode."""
        mode = OPTION_TO_TRV_MODE[option]
        await self._async_run_pending_gateway_command(
            "set TRV mode",
            lambda: self.coordinator.gateway.set_mini_trv_mode(self._device_id, mode),
            {"current_option": option},
        )
