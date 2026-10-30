"""Select controls for verified Salus thermostat settings."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .coordinator import SalusConfigEntry, SalusDataUpdateCoordinator
from .entity import SalusEntity, async_setup_salus_platform_entities
from .floor_backup import mark_floor_backup_confirmed, persist_floor_backup
from .comfort_rule import SIGNAL_COMFORT_STATUS

PARALLEL_UPDATES = 1
_OPTIONS = ("off", "level_1", "level_2", "level_3")
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SalusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Discover floor-comfort controls for client-verified devices."""
    async_setup_salus_platform_entities(
        config_entry, async_add_entities, SalusComfortWarmFloorSelect,
        lambda data: {
            device_id: device
            for device_id, device in data.climate_devices.items()
            if getattr(device, "supports_comfort_warm_floor", False)
        },
    )


class SalusComfortWarmFloorSelect(SalusEntity, SelectEntity):
    """Change floor comfort while displaying only gateway-reported state."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = True
    _attr_translation_key = "comfort_warm_floor"
    _attr_icon = "mdi:heating-coil"
    _attr_options = list(_OPTIONS)
    _data_collection = "climate_devices"

    def __init__(self, coordinator: SalusDataUpdateCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_comfort_warm_floor"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_COMFORT_STATUS, self.async_write_ha_state))
        controller = self.hass.data.get("salus_comfort_rules")
        if controller is not None and self.available:
            await controller.async_observe(self.entity_id, self.current_option)

    @property
    def extra_state_attributes(self) -> dict:
        controller = getattr(self, "hass", None) and self.hass.data.get("salus_comfort_rules")
        return controller.entity_status(self.entity_id, self.current_option) if controller is not None and self.entity_id else {}

    @property
    def current_option(self) -> str | None:
        """Return the confirmed level, never an optimistic write result."""
        settings = self._device_attr("advanced_settings")
        level = getattr(settings, "comfort_warm_floor", None)
        if type(level) is int and 0 <= level <= 3:
            return _OPTIONS[level]
        return None

    @property
    def available(self) -> bool:
        """Reject controls whose profile is no longer client-verified."""
        return (
            super().available
            and bool(self._device_attr("supports_comfort_warm_floor", False))
            and self.current_option is not None
        )

    async def async_select_option(self, option: str) -> None:
        """Request a level change and refresh reported state."""
        if option not in _OPTIONS:
            raise ServiceValidationError("Unknown Comfort Warm Floor option")
        if not self.available:
            raise ServiceValidationError("Comfort Warm Floor control is unavailable")

        backup_path: str | None = None

        async def save_backup(snapshot: dict) -> None:
            nonlocal backup_path
            key = sha256(self._device_id.encode()).hexdigest()[:24]
            backup_path = self.hass.config.path(".storage", f"salus_floor_backup_{key}.json")
            try:
                await self.hass.async_add_executor_job(persist_floor_backup,
                    backup_path, {
                    "saved_at": datetime.now(UTC).isoformat(),
                    "pending": True,
                    "requested_level": _OPTIONS.index(option),
                    "before": snapshot,
                })
            except Exception as error:
                raise HomeAssistantError(f"Floor-comfort backup failed; no command was sent: {error}") from error

        try:
            await self._async_run_gateway_command(
                "set comfort warm floor",
                lambda: self.coordinator.gateway.set_climate_device_comfort_warm_floor(
                    self._device_id, _OPTIONS.index(option),
                    before_write=save_backup, confirmation_timeout=120,
                ),
                timeout=150,
            )
        except ServiceValidationError:
            raise
        except HomeAssistantError:
            # A lost reply may follow an applied command. Refresh, never replay.
            await self.coordinator.async_request_debounced_refresh()
            raise
        if backup_path is not None:
            try:
                await self.hass.async_add_executor_job(mark_floor_backup_confirmed, backup_path)
            except Exception:
                # The command is confirmed. Retain the pending journal rather
                # than suggesting a retry of an already applied command.
                _LOGGER.exception("Floor comfort was confirmed but its backup journal could not be finalized")
        await self.coordinator.async_request_debounced_refresh()
