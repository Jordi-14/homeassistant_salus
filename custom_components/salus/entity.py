"""Base entity helpers for the Salus iT600 integration."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from salus_it600.exceptions import IT600CommandError, IT600ConnectionError

from .const import DOMAIN
from .coordinator import SalusConfigEntry, SalusData, SalusDataUpdateCoordinator

CHILD_ENTITY_TRANSLATION_KEY_BY_DEVICE_CLASS = {
    "battery": "battery",
    "energy": "energy",
    "humidity": "humidity",
    "power": "power",
    "problem": "problem",
    "temperature": "temperature",
    "window": "open_window",
}

CHILD_ENTITY_TRANSLATION_KEY_BY_UNIQUE_ID_SUFFIX = (
    ("_battery_error", "battery_problem"),
    ("_battery_problem", "battery_problem"),
    ("_floor_temperature", "floor_temperature"),
    ("_low_battery", "low_battery"),
    ("_open_window", "open_window"),
    ("_battery", "battery"),
    ("_energy", "energy"),
    ("_humidity", "humidity"),
    ("_power", "power"),
    ("_problem", "problem"),
)
PENDING_STATE_TIMEOUT_SECONDS = 30.0
_NO_PENDING = object()


@dataclass(slots=True)
class _PendingStateValue:
    """One optimistic Home Assistant-facing value."""

    value: Any
    request_id: int
    expires_at: float


class SalusEntity(CoordinatorEntity[SalusDataUpdateCoordinator]):
    """Base class for Salus entities."""

    _attr_has_entity_name = True
    _data_collection: str | None = None

    def __init__(
        self,
        coordinator: SalusDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = device_id
        self._pending_state: dict[str, _PendingStateValue] = {}
        self._pending_state_request_id = 0

    @property
    def _device(self) -> Any | None:
        """Return the current Salus device snapshot."""
        if self._data_collection is None:
            raise NotImplementedError
        data = self.coordinator.data
        if data is None:
            return None
        return getattr(data, self._data_collection).get(self._device_id)

    def _device_attr(self, attr: str, default: Any = None) -> Any:
        """Return one attribute from the current device snapshot."""
        device = self._device
        return default if device is None else getattr(device, attr, default)

    def _loop_time(self) -> float:
        """Return the event-loop monotonic time."""
        loop = getattr(getattr(self, "hass", None), "loop", None)
        if loop is not None:
            return loop.time()
        return asyncio.get_running_loop().time()

    def _pending_values_match(self, pending_value: Any, reported_value: Any) -> bool:
        """Return whether a reported value confirms a pending value."""
        return pending_value == reported_value

    def _async_write_state_if_added(self) -> None:
        """Write state only once Home Assistant has registered the entity."""
        if getattr(self, "hass", None) is None or self.entity_id is None:
            return
        self.async_write_ha_state()

    def _set_pending_state(
        self,
        values: Mapping[str, Any],
        *,
        timeout: float = PENDING_STATE_TIMEOUT_SECONDS,
    ) -> tuple[int, tuple[str, ...]]:
        """Store optimistic Home Assistant-facing values."""
        self._pending_state_request_id += 1
        request_id = self._pending_state_request_id
        keys = tuple(values)
        expires_at = self._loop_time() + timeout
        for key, value in values.items():
            self._pending_state[key] = _PendingStateValue(
                value=value,
                request_id=request_id,
                expires_at=expires_at,
            )
        if values:
            self._async_write_state_if_added()
        return request_id, keys

    def _clear_pending_state(
        self,
        *,
        request_id: int | None = None,
        keys: tuple[str, ...] | None = None,
    ) -> None:
        """Clear pending state values."""
        candidate_keys = keys or tuple(self._pending_state)
        for key in candidate_keys:
            pending = self._pending_state.get(key)
            if pending is None:
                continue
            if request_id is not None and pending.request_id != request_id:
                continue
            self._pending_state.pop(key, None)

    def _pending_command_is_current(
        self,
        request_id: int,
        keys: tuple[str, ...],
    ) -> bool:
        """Return whether a debounced command is still the newest request."""
        return all(
            (pending := self._pending_state.get(key)) is not None
            and pending.request_id == request_id
            for key in keys
        )

    def _clear_expired_pending_state(self) -> None:
        """Clear pending state values that have timed out."""
        now = self._loop_time()
        expired_keys = [
            key for key, pending in self._pending_state.items() if now >= pending.expires_at
        ]
        for key in expired_keys:
            self._pending_state.pop(key, None)

    def _fresh_pending_state_value(
        self,
        key: str,
        reported_value: Any,
        *,
        equivalent: Callable[[Any, Any], bool] | None = None,
    ) -> Any:
        """Return a fresh pending value, or a sentinel when no value is pending."""
        pending = self._pending_state.get(key)
        if pending is None:
            return _NO_PENDING

        if self._loop_time() >= pending.expires_at:
            self._pending_state.pop(key, None)
            return _NO_PENDING

        value_matches = equivalent or self._pending_values_match
        if value_matches(pending.value, reported_value):
            self._pending_state.pop(key, None)
            return _NO_PENDING

        return pending.value

    def _pending_or_reported(
        self,
        key: str,
        reported_value: Any,
        *,
        equivalent: Callable[[Any, Any], bool] | None = None,
    ) -> Any:
        """Return a pending HA-facing value or the reported gateway value."""
        pending_value = self._fresh_pending_state_value(
            key,
            reported_value,
            equivalent=equivalent,
        )
        return reported_value if pending_value is _NO_PENDING else pending_value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._clear_expired_pending_state()
        super()._handle_coordinator_update()

    def _parent_device_name(
        self,
        parent_unique_id: str,
        *,
        exclude_unique_id: str | None = None,
    ) -> str | None:
        """Return the name of a parent device from the current data snapshot."""
        data = self.coordinator.data
        if data is None:
            return None

        for collection in (
            data.climate_devices,
            data.switch_devices,
            data.cover_devices,
            data.binary_sensor_devices,
            data.sensor_devices,
        ):
            device = collection.get(parent_unique_id)
            if getattr(device, "unique_id", None) == exclude_unique_id:
                continue
            name = getattr(device, "name", None)
            if isinstance(name, str):
                return name

        for device in data.sensor_devices.values():
            if getattr(device, "unique_id", None) == exclude_unique_id:
                continue
            if getattr(device, "parent_unique_id", None):
                continue
            device_data = getattr(device, "data", None)
            if not isinstance(device_data, dict):
                continue
            if device_data.get("UniID") == parent_unique_id:
                name = getattr(device, "name", None)
                if isinstance(name, str):
                    return name

        return None

    def _child_entity_translation_key(self, device: Any) -> str | None:
        """Return the translation key for a child entity."""
        parent_unique_id = getattr(device, "parent_unique_id", None)
        if not parent_unique_id:
            return None

        unique_id = getattr(device, "unique_id", self._device_id)
        if isinstance(unique_id, str):
            suffix_keys = CHILD_ENTITY_TRANSLATION_KEY_BY_UNIQUE_ID_SUFFIX
            for suffix, translation_key in suffix_keys:
                if unique_id.endswith(suffix):
                    return translation_key

        device_class = getattr(device, "device_class", None)
        if isinstance(device_class, str):
            return CHILD_ENTITY_TRANSLATION_KEY_BY_DEVICE_CLASS.get(device_class)

        return None

    def _child_entity_fallback_name(self, device: Any) -> str | None:
        """Return a fallback short name for an unknown child entity."""
        parent_unique_id = getattr(device, "parent_unique_id", None)
        if not parent_unique_id:
            return None

        raw_name = getattr(device, "name", None)
        parent_name = self._parent_device_name(
            parent_unique_id,
            exclude_unique_id=getattr(device, "unique_id", self._device_id),
        )
        if not isinstance(raw_name, str) or not isinstance(parent_name, str):
            return None

        if not raw_name.startswith(parent_name):
            return None

        child_name = raw_name.removeprefix(parent_name).strip()
        if child_name:
            return child_name

        return None

    def _set_child_entity_name_metadata(self, device: Any | None) -> None:
        """Set translated or fallback naming metadata for a child entity."""
        if device is None or not getattr(device, "parent_unique_id", None):
            self._attr_name = None
            return

        if translation_key := self._child_entity_translation_key(device):
            self._attr_translation_key = translation_key
            return

        if fallback_name := self._child_entity_fallback_name(device):
            self._attr_name = fallback_name

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

    async def _async_run_gateway_command_and_refresh(
        self,
        action: str,
        command: Callable[[], Awaitable[None]],
    ) -> None:
        """Run one gateway command and request the normal post-command refresh."""
        await self._async_run_gateway_command(action, command)
        await self.coordinator.async_request_debounced_refresh()

    async def _async_run_pending_gateway_command(
        self,
        action: str,
        command: Callable[[], Awaitable[None]],
        pending_state: Mapping[str, Any],
        *,
        debounce_seconds: float = 0.0,
        refresh: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        """Run a gateway command with optimistic Home Assistant-facing state."""
        request_id, keys = self._set_pending_state(pending_state)

        if debounce_seconds > 0:
            await asyncio.sleep(debounce_seconds)
            if not self._pending_command_is_current(request_id, keys):
                return

        try:
            await self._async_run_gateway_command(action, command)
        except Exception:
            self._clear_pending_state(request_id=request_id, keys=keys)
            self._async_write_state_if_added()
            raise

        if refresh is None:
            await self.coordinator.async_request_debounced_refresh()
        else:
            await refresh()

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
    config_entry: SalusConfigEntry,
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
        async_add_entities(
            [entity_factory(device_id) for device_id in sorted(new_device_ids)]
        )

    _async_add_new_entities()
    config_entry.async_on_unload(
        coordinator.async_add_listener(_async_add_new_entities)
    )


def async_setup_salus_platform_entities(
    config_entry: SalusConfigEntry,
    async_add_entities: Callable[[list[SalusEntity]], None],
    entity_factory: Callable[[SalusDataUpdateCoordinator, str], SalusEntity],
    devices_getter: Callable[[SalusData], Mapping[str, Any]],
) -> None:
    """Set up one Salus platform using the shared entity discovery helper."""
    coordinator = config_entry.runtime_data.coordinator

    async_add_salus_entities(
        config_entry,
        coordinator,
        async_add_entities,
        lambda device_id: entity_factory(coordinator, device_id),
        devices_getter,
    )
