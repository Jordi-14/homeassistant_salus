"""Coordinator for Salus iT600 gateway data."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from salus_it600.exceptions import IT600AuthenticationError, IT600ConnectionError
from salus_it600.gateway import IT600Gateway

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SalusData:
    """Latest device snapshots from a Salus gateway."""

    climate_devices: dict[str, Any]
    binary_sensor_devices: dict[str, Any]
    switch_devices: dict[str, Any]
    cover_devices: dict[str, Any]
    sensor_devices: dict[str, Any]
    raw_climate_props: dict[str, dict[str, Any]]


@dataclass(slots=True)
class SalusRuntimeData:
    """Runtime objects for a Salus config entry."""

    gateway: IT600Gateway
    coordinator: SalusDataUpdateCoordinator


def is_sq610_device(device: Any) -> bool:
    """Return whether the device is a Quantum thermostat."""
    model = getattr(device, "model", None)
    return isinstance(model, str) and "SQ610" in model.upper()


def flatten_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested gateway payload dictionaries into a single key/value map."""
    flattened: dict[str, Any] = {}

    def _walk(value: Any) -> None:
        if not isinstance(value, dict):
            return

        for nested_key, nested_value in value.items():
            if isinstance(nested_value, dict):
                _walk(nested_value)
            else:
                flattened[nested_key] = nested_value

    _walk(data)
    return flattened


class SalusDataUpdateCoordinator(DataUpdateCoordinator[SalusData]):
    """Coordinate all Salus gateway polling through one request path."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        gateway: IT600Gateway,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=config_entry,
        )
        self.gateway = gateway
        self.gateway_lock = asyncio.Lock()
        self.gateway_id: str | None = None

    async def _async_update_data(self) -> SalusData:
        """Fetch all Salus device data from the gateway."""
        try:
            async with asyncio.timeout(10):
                async with self.gateway_lock:
                    await self.gateway.poll_status()
                    climate_devices = dict(self.gateway.get_climate_devices() or {})
                    raw_climate_props = await self._async_fetch_raw_climate_props(
                        climate_devices
                    )

                    return SalusData(
                        climate_devices=climate_devices,
                        binary_sensor_devices=dict(
                            self.gateway.get_binary_sensor_devices() or {}
                        ),
                        switch_devices=dict(self.gateway.get_switch_devices() or {}),
                        cover_devices=dict(self.gateway.get_cover_devices() or {}),
                        sensor_devices=dict(self.gateway.get_sensor_devices() or {}),
                        raw_climate_props=raw_climate_props,
                    )
        except IT600AuthenticationError as ex:
            raise ConfigEntryAuthFailed("Invalid Salus gateway EUID") from ex
        except (IT600ConnectionError, TimeoutError) as ex:
            raise UpdateFailed(f"Salus gateway is unavailable: {ex}") from ex

    async def _async_fetch_raw_climate_props(
        self,
        climate_devices: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        """Fetch raw SQ610 properties not exposed by salus_it600 models."""
        sq610_devices = [
            device for device in climate_devices.values() if is_sq610_device(device)
        ]
        if not sq610_devices:
            return {}

        try:
            response = await self.gateway._make_encrypted_request(  # noqa: SLF001
                "read",
                {
                    "requestAttr": "deviceid",
                    "id": [{"data": device.data} for device in sq610_devices],
                },
            )
        except Exception:  # noqa: BLE001
            _LOGGER.warning(
                "Failed to read raw SQ610 climate properties; using last known values",
                exc_info=True,
            )
            return self.data.raw_climate_props if self.data is not None else {}

        raw_climate_props = {}
        for device_status in response.get("id", []):
            unique_id = device_status.get("data", {}).get("UniID")
            if unique_id is not None:
                raw_climate_props[unique_id] = flatten_dict(device_status)

        return raw_climate_props
