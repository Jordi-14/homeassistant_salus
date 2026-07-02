"""Coordinator for Salus iT600 gateway data."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, UTC, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from salus_it600.exceptions import IT600AuthenticationError, IT600ConnectionError
from salus_it600.gateway import IT600Gateway
from salus_it600.device_models import is_sq610_model

from .const import (
    CONF_POLL_FAILURE_THRESHOLD,
    CONF_POST_COMMAND_REFRESH_DELAY,
    CONF_SCAN_INTERVAL,
    DEFAULT_POLL_FAILURE_THRESHOLD,
    DEFAULT_POST_COMMAND_REFRESH_DELAY,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    GATEWAY_OPERATION_TIMEOUT_SECONDS,
    MAX_POST_COMMAND_REFRESH_DELAY,
    MAX_SCAN_INTERVAL_SECONDS,
    MIN_POST_COMMAND_REFRESH_DELAY,
    MIN_SCAN_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

ISSUE_GATEWAY_UNAVAILABLE = "gateway_unavailable"
TROUBLESHOOTING_URL = "https://github.com/Jordi-14/homeassistant_salus#troubleshooting"


def _utcnow_iso() -> str:
    """Return a UTC timestamp suitable for diagnostics."""
    return datetime.now(UTC).isoformat()


def _exception_summary(ex: Exception) -> str:
    """Return a compact exception summary for diagnostics."""
    return f"{type(ex).__name__}: {ex}"


def _scan_interval_from_options(options: Mapping[str, Any]) -> timedelta:
    """Return the configured coordinator scan interval."""
    return timedelta(
        seconds=_clamped_option(
            options,
            CONF_SCAN_INTERVAL,
            DEFAULT_SCAN_INTERVAL_SECONDS,
            minimum=MIN_SCAN_INTERVAL_SECONDS,
            maximum=MAX_SCAN_INTERVAL_SECONDS,
            value_type=int,
        )
    )


def _clamped_option(
    options: Mapping[str, Any],
    key: str,
    default: int | float,
    *,
    minimum: int | float | None = None,
    maximum: int | float | None = None,
    value_type: type[int] | type[float] = int,
) -> int | float:
    """Return one numeric option with default and bounds applied."""
    try:
        value = value_type(options.get(key, default))
    except (TypeError, ValueError):
        return default

    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


@dataclass(slots=True)
class SalusGatewayHealth:
    """Runtime gateway health counters for diagnostics."""

    successful_updates: int = 0
    failed_updates: int = 0
    consecutive_update_failures: int = 0
    last_successful_update_at: str | None = None
    last_failed_update_at: str | None = None
    last_update_error: str | None = None

    def as_diagnostics(self) -> dict[str, Any]:
        """Return a serializable diagnostic view."""
        return asdict(self)


@dataclass(slots=True)
class SalusDeviceAvailability:
    """Runtime device availability history for support diagnostics."""

    device_id: str
    platform: str
    name: str | None
    model: str | None
    available: bool
    online_status: Any
    online_status_source: str
    first_seen_at: str
    last_checked_at: str
    last_seen_online_at: str | None
    consecutive_missed_refreshes: int

    def as_diagnostics(self) -> dict[str, Any]:
        """Return a serializable diagnostic view."""
        diagnostics = asdict(self)
        diagnostics.pop("device_id")
        return diagnostics


@dataclass(slots=True)
class SalusData:
    """Latest device snapshots from a Salus gateway."""

    climate_devices: dict[str, Any]
    binary_sensor_devices: dict[str, Any]
    switch_devices: dict[str, Any]
    cover_devices: dict[str, Any]
    sensor_devices: dict[str, Any]


@dataclass(slots=True)
class SalusRuntimeData:
    """Runtime objects for a Salus config entry."""

    gateway: IT600Gateway
    coordinator: SalusDataUpdateCoordinator


type SalusConfigEntry = ConfigEntry[SalusRuntimeData]


def is_sq610_device(device: Any) -> bool:
    """Return whether the device is a Quantum thermostat."""
    return is_sq610_model(getattr(device, "model", None))


def _iter_device_collections(
    data: SalusData,
) -> Iterator[tuple[str, Mapping[str, Any]]]:
    """Yield every device collection in a Salus data snapshot."""
    yield "climate", data.climate_devices
    yield "binary_sensor", data.binary_sensor_devices
    yield "switch", data.switch_devices
    yield "cover", data.cover_devices
    yield "sensor", data.sensor_devices


def _device_available(device: Any) -> bool:
    """Return the normalized device availability flag."""
    return bool(getattr(device, "available", True))


def _device_online_status(device: Any) -> tuple[Any, str]:
    """Return normalized or inferred online status for diagnostics."""
    online_status = getattr(device, "online_status", None)
    if online_status is not None:
        return online_status, "normalized_online_status"

    diagnostic_fields = getattr(device, "diagnostic_fields", None)
    if isinstance(diagnostic_fields, dict) and "OnlineStatus_i" in diagnostic_fields:
        return diagnostic_fields["OnlineStatus_i"], "diagnostic_fields"

    device_data = getattr(device, "data", None)
    if isinstance(device_data, dict):
        if "OnlineStatus_i" in device_data:
            return device_data["OnlineStatus_i"], "device_data"

        zdo_info = device_data.get("sZDOInfo")
        if isinstance(zdo_info, dict) and "OnlineStatus_i" in zdo_info:
            return zdo_info["OnlineStatus_i"], "device_data"

    return int(_device_available(device)), "device_available"


class SalusDataUpdateCoordinator(DataUpdateCoordinator[SalusData]):
    """Coordinate all Salus gateway polling through one request path."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SalusConfigEntry,
        gateway: IT600Gateway,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=_scan_interval_from_options(config_entry.options),
            config_entry=config_entry,
            always_update=False,
        )
        self.gateway = gateway
        self._config_entry = config_entry
        self.gateway_lock = asyncio.Lock()
        self.gateway_id: str | None = None
        self._debounced_refresh_task: asyncio.Task[None] | None = None
        self._post_command_refresh_requested_at: float | None = None
        self._gateway_health = SalusGatewayHealth()
        self._device_availability: dict[str, SalusDeviceAvailability] = {}

    def gateway_diagnostics(self) -> dict[str, Any]:
        """Return gateway health diagnostics."""
        diagnostics = self._gateway_health.as_diagnostics()
        diagnostics["poll_failure_threshold"] = self._poll_failure_threshold()
        diagnostics["scan_interval_seconds"] = int(
            _scan_interval_from_options(self._config_entry.options).total_seconds()
        )
        diagnostics["post_command_refresh_delay_seconds"] = (
            self._post_command_refresh_delay()
        )
        return diagnostics

    def device_availability_diagnostics(self) -> dict[str, dict[str, Any]]:
        """Return device availability history diagnostics."""
        return {
            device_id: status.as_diagnostics()
            for device_id, status in sorted(self._device_availability.items())
        }

    async def async_request_debounced_refresh(self) -> None:
        """Request a delayed refresh after a gateway write.

        Rapid commands update the requested timestamp. The running task uses the
        latest timestamp, so slider-style changes collapse into one refresh
        after the most recent command.
        """
        self._post_command_refresh_requested_at = self._loop_time()

        if self._debounced_refresh_task is None or self._debounced_refresh_task.done():
            self._debounced_refresh_task = asyncio.create_task(
                self._async_debounced_refresh()
            )

    async def _async_debounced_refresh(self) -> None:
        """Run the delayed post-command refresh."""
        try:
            while True:
                request_at = self._post_command_refresh_requested_at
                if request_at is None:
                    return

                settle_delay = self._post_command_refresh_delay()
                await self._async_sleep_until(request_at + settle_delay)
                if self._post_command_refresh_requested_at != request_at:
                    continue

                await self.async_request_refresh()
                if self._post_command_refresh_requested_at != request_at:
                    continue

                self._post_command_refresh_requested_at = None
                return
        except Exception:
            _LOGGER.exception("Debounced Salus refresh failed")
            self._post_command_refresh_requested_at = None
        finally:
            current_task = asyncio.current_task()
            if self._debounced_refresh_task is current_task:
                self._debounced_refresh_task = None

    async def _async_sleep_until(self, when: float) -> None:
        """Sleep until a Home Assistant loop timestamp."""
        delay = when - self._loop_time()
        if delay > 0:
            await asyncio.sleep(delay)

    def _loop_time(self) -> float:
        """Return monotonic time from the Home Assistant event loop."""
        loop = getattr(self.hass, "loop", None)
        if loop is not None:
            return loop.time()
        return asyncio.get_running_loop().time()

    def async_cancel_debounced_refresh(self) -> None:
        """Cancel a pending debounced refresh task, if one exists."""
        if (
            self._debounced_refresh_task is not None
            and not self._debounced_refresh_task.done()
        ):
            self._debounced_refresh_task.cancel()
        self._debounced_refresh_task = None
        self._post_command_refresh_requested_at = None

    async def _async_update_data(self) -> SalusData:
        """Fetch all Salus device data from the gateway."""
        try:
            async with asyncio.timeout(GATEWAY_OPERATION_TIMEOUT_SECONDS):
                async with self.gateway_lock:
                    await self.gateway.poll_status()
                    climate_devices = dict(self.gateway.get_climate_devices() or {})

                    data = SalusData(
                        climate_devices=climate_devices,
                        binary_sensor_devices=dict(
                            self.gateway.get_binary_sensor_devices() or {}
                        ),
                        switch_devices=dict(self.gateway.get_switch_devices() or {}),
                        cover_devices=dict(self.gateway.get_cover_devices() or {}),
                        sensor_devices=dict(self.gateway.get_sensor_devices() or {}),
                    )

                    self._update_device_availability(data)
                    self._record_update_success()
                    return data
        except IT600AuthenticationError as ex:
            self._record_update_failure(ex)
            raise ConfigEntryAuthFailed("Invalid Salus gateway EUID") from ex
        except (IT600ConnectionError, TimeoutError) as ex:
            self._record_update_failure(ex)
            cached_data = self.data
            threshold = self._poll_failure_threshold()
            if (
                cached_data is not None
                and threshold > 0
                and self._gateway_health.consecutive_update_failures < threshold
            ):
                _LOGGER.debug(
                    "Keeping last Salus data after poll failure %s/%s: %s",
                    self._gateway_health.consecutive_update_failures,
                    threshold,
                    ex,
                )
                return cached_data
            self._async_create_gateway_unavailable_issue()
            raise UpdateFailed(f"Salus gateway is unavailable: {ex}") from ex
        except Exception as ex:
            self._record_update_failure(ex)
            raise

    def _poll_failure_threshold(self) -> int:
        """Return configured consecutive poll failures before marking unavailable."""
        return int(
            _clamped_option(
                getattr(self._config_entry, "options", {}),
                CONF_POLL_FAILURE_THRESHOLD,
                DEFAULT_POLL_FAILURE_THRESHOLD,
                minimum=0,
                value_type=int,
            )
        )

    def _post_command_refresh_delay(self) -> float:
        """Return configured settle-refresh delay after a gateway write."""
        return float(
            _clamped_option(
                getattr(self._config_entry, "options", {}),
                CONF_POST_COMMAND_REFRESH_DELAY,
                DEFAULT_POST_COMMAND_REFRESH_DELAY,
                minimum=MIN_POST_COMMAND_REFRESH_DELAY,
                maximum=MAX_POST_COMMAND_REFRESH_DELAY,
                value_type=float,
            )
        )

    def _record_update_success(self) -> None:
        """Record a successful coordinator update."""
        health = self._gateway_health
        health.successful_updates += 1
        health.consecutive_update_failures = 0
        health.last_successful_update_at = _utcnow_iso()
        health.last_update_error = None
        self._async_delete_gateway_unavailable_issue()

    def _record_update_failure(self, ex: Exception) -> None:
        """Record a failed coordinator update."""
        health = self._gateway_health
        health.failed_updates += 1
        health.consecutive_update_failures += 1
        health.last_failed_update_at = _utcnow_iso()
        health.last_update_error = _exception_summary(ex)

    def _gateway_unavailable_issue_id(self) -> str:
        """Return the repairs issue ID for this config entry."""
        entry_id = getattr(self._config_entry, "entry_id", "gateway")
        return f"{entry_id}_{ISSUE_GATEWAY_UNAVAILABLE}"

    def _async_create_gateway_unavailable_issue(self) -> None:
        """Create an actionable repairs issue for persistent gateway failures."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self._gateway_unavailable_issue_id(),
            is_fixable=False,
            is_persistent=False,
            learn_more_url=TROUBLESHOOTING_URL,
            severity=ir.IssueSeverity.ERROR,
            translation_key=ISSUE_GATEWAY_UNAVAILABLE,
            translation_placeholders={
                "host": str(self._config_entry.data.get(CONF_HOST, "configured host")),
            },
        )

    def _async_delete_gateway_unavailable_issue(self) -> None:
        """Remove the gateway-unavailable repairs issue after recovery."""
        ir.async_delete_issue(
            self.hass,
            DOMAIN,
            self._gateway_unavailable_issue_id(),
        )

    def _update_device_availability(self, data: SalusData) -> None:
        """Update per-device availability history from one successful poll."""
        checked_at = _utcnow_iso()
        current_device_ids: set[str] = set()

        for platform, devices in _iter_device_collections(data):
            for device_id, device in devices.items():
                current_device_ids.add(device_id)
                available = _device_available(device)
                online_status, online_status_source = _device_online_status(device)
                status = self._device_availability.get(device_id)

                if status is None:
                    status = SalusDeviceAvailability(
                        device_id=device_id,
                        platform=platform,
                        name=getattr(device, "name", None),
                        model=getattr(device, "model", None),
                        available=available,
                        online_status=online_status,
                        online_status_source=online_status_source,
                        first_seen_at=checked_at,
                        last_checked_at=checked_at,
                        last_seen_online_at=checked_at if available else None,
                        consecutive_missed_refreshes=0 if available else 1,
                    )
                    self._device_availability[device_id] = status
                    continue

                status.platform = platform
                status.name = getattr(device, "name", None)
                status.model = getattr(device, "model", None)
                status.available = available
                status.online_status = online_status
                status.online_status_source = online_status_source
                status.last_checked_at = checked_at

                if available:
                    status.last_seen_online_at = checked_at
                    status.consecutive_missed_refreshes = 0
                else:
                    status.consecutive_missed_refreshes += 1

        for device_id, status in self._device_availability.items():
            if device_id in current_device_ids:
                continue

            status.available = False
            status.online_status = None
            status.online_status_source = "missing_from_snapshot"
            status.last_checked_at = checked_at
            status.consecutive_missed_refreshes += 1
