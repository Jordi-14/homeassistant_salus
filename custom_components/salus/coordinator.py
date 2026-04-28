"""Coordinator for Salus iT600 gateway data.

This module implements the DataUpdateCoordinator pattern for polling the Salus iT600
gateway at regular intervals (default 10 seconds) and aggregating device state into a
single SalusData snapshot.

Architecture:
    poll_status() flow:
    1. Coordinator schedules _async_update_data() every 10 seconds
    2. _async_update_data() locks gateway (prevents concurrent requests)
    3. gateway.poll_status() fetches all device types (climate, binary_sensor, etc.)
    4. Device type lists extracted and packaged into SalusData dataclass
    5. SQ610 raw props fetched separately (protocol quirk workaround)
    6. Coordinator notifies all listening platforms (climate, switch, etc.)
    7. Platforms' _handle_coordinator_update() callback triggered
    8. Entities update their UI representation from coordinator.data

Data Flow:
    SalusData (immutable snapshot):
    - climate_devices: dict[unique_id] → ClimateDevice
    - binary_sensor_devices: dict[unique_id] → BinarySensorDevice
    - switch_devices: dict[unique_id] → SwitchDevice
    - cover_devices: dict[unique_id] → CoverDevice
    - sensor_devices: dict[unique_id] → SensorDevice
    - raw_climate_props: dict[unique_id] → SQ610-specific raw payload fields

All platforms access coordinator.data to get current device state. When data changes,
platforms are notified and entities read from the new snapshot.

Error Handling:
    - IT600AuthenticationError: Raised on config entry auth failure (EUID mismatch)
    - IT600ConnectionError/TimeoutError: Raised as UpdateFailed (recoverable)
    - Exception: Logged with warning for raw SQ610 props (non-blocking fallback)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from salus_it600.exceptions import (
    IT600AuthenticationError,
    IT600CommandError,
    IT600ConnectionError,
)
from salus_it600.gateway import IT600Gateway
from salus_it600.device_models import is_sq610_model

from .const import DEFAULT_REFRESH_DEBOUNCE, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SalusData:
    """Latest device snapshots from a Salus gateway.

    Immutable snapshot of all device states as of the last coordinator update.
    Shared by all platforms and entities for this config entry.

    Attributes:
        climate_devices: Climate entities (thermostats, fan coils) by unique_id
        binary_sensor_devices: Binary sensors (doors, windows, etc.) by unique_id
        switch_devices: Switches (relays) by unique_id
        cover_devices: Covers (blinds) by unique_id
        sensor_devices: Sensors (temperature, humidity) by unique_id
        raw_climate_props: SQ610 Quantum thermostat raw protocol fields (workaround for
            protocol quirks like humidity in SunnySetpoint_x100). Maps unique_id → dict
            of flattened payload fields not exposed by salus_it600 models.
    """

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
    return is_sq610_model(getattr(device, "model", None))


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
        self._refresh_debounce_delay = DEFAULT_REFRESH_DEBOUNCE
        self._debounced_refresh_task: asyncio.Task[None] | None = None

    async def async_request_debounced_refresh(self) -> None:
        """Request one refresh after collapsing rapid write-triggered requests."""
        if (
            self._debounced_refresh_task is not None
            and not self._debounced_refresh_task.done()
        ):
            return

        self._debounced_refresh_task = asyncio.create_task(
            self._async_debounced_refresh()
        )

    async def _async_debounced_refresh(self) -> None:
        """Run the delayed refresh task."""
        try:
            await asyncio.sleep(self._refresh_debounce_delay)
            await self.async_request_refresh()
        except Exception:
            _LOGGER.exception("Debounced Salus refresh failed")
        finally:
            current_task = asyncio.current_task()
            if self._debounced_refresh_task is current_task:
                self._debounced_refresh_task = None

    def async_cancel_debounced_refresh(self) -> None:
        """Cancel a pending debounced refresh task, if one exists."""
        if (
            self._debounced_refresh_task is not None
            and not self._debounced_refresh_task.done()
        ):
            self._debounced_refresh_task.cancel()
        self._debounced_refresh_task = None

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
        """Fetch raw SQ610 properties not exposed by salus_it600 models.

        SQ610 Quantum thermostats have unusual protocol quirks:
        - Humidity stored in SunnySetpoint_x100 field (not standard humidity field)
        - Write property names differ from read property names
        - Dual setpoints (heating vs cooling) based on system mode

        salus_it600.gateway.py handles most quirks internally, but this integration
        needs raw payload access for certain SQ610-specific features (e.g., custom
        preset mapping). This method makes an additional encrypted request to fetch
        raw SQ610 device data and flatten it for use by climate.py.

        Non-blocking: If this call fails, it logs a warning and returns last known
        values or empty dict. The main poll_status() succeeds regardless.

        Args:
            climate_devices: Climate devices from coordinator.data to check for SQ610

        Returns:
            dict[unique_id] → flattened raw payload fields for SQ610 devices,
            or previous values if fetch fails
        """
        sq610_devices = [
            device for device in climate_devices.values() if is_sq610_device(device)
        ]
        if not sq610_devices:
            return {}

        try:
            return await self.gateway.fetch_sq610_properties(
                [device.unique_id for device in sq610_devices],
            )
        except (IT600CommandError, IT600ConnectionError, TimeoutError) as ex:
            _LOGGER.warning(
                "Failed to read raw SQ610 climate properties: %s; "
                "using last known values",
                ex,
            )
            return self.data.raw_climate_props if self.data is not None else {}
        except Exception:
            _LOGGER.exception(
                "Unexpected error while reading raw SQ610 climate properties; "
                "using last known values",
            )
            return self.data.raw_climate_props if self.data is not None else {}
