"""Coordinator tests."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from salus_it600.exceptions import (
    IT600AuthenticationError,
    IT600ConnectionError,
)

from custom_components.salus.const import (
    CONF_POLL_FAILURE_THRESHOLD,
    CONF_POST_COMMAND_REFRESH_DELAY,
    CONF_SCAN_INTERVAL,
)
from custom_components.salus.coordinator import (
    SalusDataUpdateCoordinator,
)


def _device(device_id: str, model: str = "SQ610RF") -> SimpleNamespace:
    return SimpleNamespace(
        unique_id=device_id,
        available=True,
        name=device_id,
        model=model,
        data={"UniID": device_id},
        online_status=1,
        diagnostic_fields={"OnlineStatus_i": 1},
    )


class FakeGateway:
    """Gateway fake for coordinator unit tests."""

    def __init__(self) -> None:
        self.climate_devices = {"sq610-1": _device("sq610-1")}
        self.binary_sensor_devices: dict[str, Any] = {}
        self.switch_devices: dict[str, Any] = {}
        self.cover_devices: dict[str, Any] = {}
        self.sensor_devices: dict[str, Any] = {}
        self.poll_error: Exception | None = None

    async def poll_status(self) -> None:
        if self.poll_error is not None:
            raise self.poll_error

    def get_climate_devices(self) -> dict[str, Any]:
        return self.climate_devices

    def get_binary_sensor_devices(self) -> dict[str, Any]:
        return self.binary_sensor_devices

    def get_switch_devices(self) -> dict[str, Any]:
        return self.switch_devices

    def get_cover_devices(self) -> dict[str, Any]:
        return self.cover_devices

    def get_sensor_devices(self) -> dict[str, Any]:
        return self.sensor_devices


def _coordinator(
    hass: HomeAssistant,
    gateway: FakeGateway,
    options: dict[str, Any] | None = None,
) -> SalusDataUpdateCoordinator:
    config_entry = MagicMock()
    config_entry.entry_id = "entry-1"
    config_entry.data = {"host": "192.0.2.10"}
    config_entry.options = options or {}
    return SalusDataUpdateCoordinator(
        hass=hass,
        config_entry=config_entry,
        gateway=gateway,
    )


async def test_scan_interval_uses_options(hass: HomeAssistant) -> None:
    coordinator = _coordinator(
        hass,
        FakeGateway(),
        options={CONF_SCAN_INTERVAL: 45},
    )

    assert coordinator.update_interval == timedelta(seconds=45)
    assert coordinator.gateway_diagnostics()["scan_interval_seconds"] == 45


async def test_scan_interval_clamps_options(hass: HomeAssistant) -> None:
    coordinator = _coordinator(
        hass,
        FakeGateway(),
        options={CONF_SCAN_INTERVAL: 1},
    )

    assert coordinator.update_interval == timedelta(seconds=10)
    assert coordinator.gateway_diagnostics()["scan_interval_seconds"] == 10


async def test_update_data_populates_snapshot(hass: HomeAssistant) -> None:
    gateway = FakeGateway()
    coordinator = _coordinator(hass, gateway)

    data = await coordinator._async_update_data()

    assert data.climate_devices == {"sq610-1": gateway.climate_devices["sq610-1"]}

    health = coordinator.gateway_diagnostics()
    assert health["successful_updates"] == 1
    assert health["consecutive_update_failures"] == 0


async def test_unchanged_snapshot_does_not_dispatch_listener_update(
    hass: HomeAssistant,
) -> None:
    gateway = FakeGateway()
    coordinator = _coordinator(hass, gateway)
    listener_updates = 0

    def _listener() -> None:
        nonlocal listener_updates
        listener_updates += 1

    remove_listener = coordinator.async_add_listener(_listener)

    await coordinator.async_refresh()
    assert listener_updates == 1

    gateway.climate_devices = {"sq610-1": _device("sq610-1")}
    await coordinator.async_refresh()
    assert listener_updates == 1

    changed_device = _device("sq610-1")
    changed_device.target_temperature = 19.0
    gateway.climate_devices = {"sq610-1": changed_device}

    await coordinator.async_refresh()
    assert listener_updates == 2

    remove_listener()


async def test_update_data_maps_auth_failure(hass: HomeAssistant) -> None:
    gateway = FakeGateway()
    gateway.poll_error = IT600AuthenticationError("bad euid")
    coordinator = _coordinator(hass, gateway)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()

    assert coordinator.gateway_diagnostics()["consecutive_update_failures"] == 1


async def test_update_data_maps_connection_failure(hass: HomeAssistant) -> None:
    gateway = FakeGateway()
    gateway.poll_error = IT600ConnectionError("offline")
    coordinator = _coordinator(hass, gateway)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert "IT600ConnectionError: offline" in coordinator.gateway_diagnostics()["last_update_error"]


async def test_connection_failures_keep_last_data_until_threshold(hass: HomeAssistant) -> None:
    gateway = FakeGateway()
    coordinator = _coordinator(hass, gateway)
    coordinator.data = await coordinator._async_update_data()

    gateway.poll_error = IT600ConnectionError("offline")

    # First two failures return stale data
    assert coordinator.data is await coordinator._async_update_data()
    assert coordinator.data is await coordinator._async_update_data()

    # Third failure exceeds threshold (default 3)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    health = coordinator.gateway_diagnostics()
    assert health["consecutive_update_failures"] == 3
    assert health["poll_failure_threshold"] == 3

    # Recovery clears failures
    gateway.poll_error = None
    await coordinator._async_update_data()


async def test_zero_threshold_marks_unavailable_immediately(hass: HomeAssistant) -> None:
    gateway = FakeGateway()
    coordinator = _coordinator(hass, gateway, options={CONF_POLL_FAILURE_THRESHOLD: 0})
    coordinator.data = await coordinator._async_update_data()

    gateway.poll_error = IT600ConnectionError("offline")

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator.gateway_diagnostics()["consecutive_update_failures"] == 1


async def test_availability_history_tracks_missing_devices(hass: HomeAssistant) -> None:
    gateway = FakeGateway()
    coordinator = _coordinator(hass, gateway)

    await coordinator._async_update_data()
    gateway.climate_devices = {}
    await coordinator._async_update_data()

    device_health = coordinator.device_availability_diagnostics()["sq610-1"]
    assert device_health["available"] is False
    assert device_health["consecutive_missed_refreshes"] == 1


async def test_debounced_refresh_coalesces_rapid_requests(hass: HomeAssistant) -> None:
    coordinator = _coordinator(
        hass,
        FakeGateway(),
        options={CONF_POST_COMMAND_REFRESH_DELAY: 0},
    )
    coordinator.refresh_count = 0
    _orig = coordinator.async_request_refresh

    async def _counting_refresh():
        coordinator.refresh_count += 1

    coordinator.async_request_refresh = _counting_refresh

    await coordinator.async_request_debounced_refresh()
    await coordinator.async_request_debounced_refresh()
    await coordinator.async_request_debounced_refresh()

    assert coordinator._debounced_refresh_task is not None
    await coordinator._debounced_refresh_task
    await asyncio.sleep(0)

    assert coordinator.refresh_count == 1
    assert coordinator._debounced_refresh_task is None


async def test_debounced_refresh_waits_for_settle_delay(hass: HomeAssistant) -> None:
    coordinator = _coordinator(
        hass,
        FakeGateway(),
        options={CONF_POST_COMMAND_REFRESH_DELAY: 0.01},
    )
    coordinator.refresh_count = 0

    async def _counting_refresh():
        coordinator.refresh_count += 1

    coordinator.async_request_refresh = _counting_refresh

    await coordinator.async_request_debounced_refresh()
    assert coordinator._debounced_refresh_task is not None
    await coordinator._debounced_refresh_task

    assert coordinator.refresh_count == 1


async def test_cancel_debounced_refresh_stops_pending_task(
    hass: HomeAssistant,
) -> None:
    coordinator = _coordinator(
        hass,
        FakeGateway(),
        options={CONF_POST_COMMAND_REFRESH_DELAY: 30},
    )
    coordinator.refresh_count = 0

    async def _counting_refresh():
        coordinator.refresh_count += 1

    coordinator.async_request_refresh = _counting_refresh

    await coordinator.async_request_debounced_refresh()
    task = coordinator._debounced_refresh_task
    assert task is not None

    coordinator.async_cancel_debounced_refresh()

    assert coordinator._debounced_refresh_task is None
    assert coordinator._post_command_refresh_requested_at is None
    with pytest.raises(asyncio.CancelledError):
        await task
    assert coordinator.refresh_count == 0


async def test_cancel_debounced_refresh_is_safe_without_pending_task(
    hass: HomeAssistant,
) -> None:
    coordinator = _coordinator(hass, FakeGateway())

    coordinator.async_cancel_debounced_refresh()

    assert coordinator._debounced_refresh_task is None
    assert coordinator._post_command_refresh_requested_at is None
