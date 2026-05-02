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
    SalusData,
    SalusDataUpdateCoordinator,
)


def _device(device_id: str, model: str = "SQ610RF") -> SimpleNamespace:
    return SimpleNamespace(
        unique_id=device_id,
        available=True,
        name=device_id,
        model=model,
        data={"UniID": device_id},
    )


class FakeGateway:
    """Gateway fake for coordinator unit tests."""

    def __init__(self) -> None:
        self.climate_devices = {"sq610-1": _device("sq610-1")}
        self.binary_sensor_devices: dict[str, Any] = {}
        self.switch_devices: dict[str, Any] = {}
        self.cover_devices: dict[str, Any] = {}
        self.sensor_devices: dict[str, Any] = {}
        self.raw_props = {"sq610-1": {"SystemMode": 3, "OnlineStatus_i": 1}}
        self.raw_fetch_ids: list[str] = []
        self.poll_error: Exception | None = None
        self.raw_error: Exception | None = None

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

    async def fetch_sq610_properties(
        self, device_ids: list[str]
    ) -> dict[str, dict[str, Any]]:
        self.raw_fetch_ids = device_ids
        if self.raw_error is not None:
            raise self.raw_error
        return self.raw_props


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
    assert data.raw_climate_props == {"sq610-1": {"SystemMode": 3, "OnlineStatus_i": 1}}
    assert gateway.raw_fetch_ids == ["sq610-1"]

    health = coordinator.gateway_diagnostics()
    assert health["successful_updates"] == 1
    assert health["consecutive_update_failures"] == 0


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


async def test_raw_sq610_failure_uses_last_known_values(hass: HomeAssistant, caplog) -> None:
    gateway = FakeGateway()
    gateway.raw_error = IT600ConnectionError("offline")
    coordinator = _coordinator(hass, gateway)
    coordinator.data = SalusData(
        climate_devices={},
        binary_sensor_devices={},
        switch_devices={},
        cover_devices={},
        sensor_devices={},
        raw_climate_props={"sq610-1": {"SystemMode": 4}},
    )

    raw_props = await coordinator._async_fetch_raw_climate_props(gateway.climate_devices)

    assert raw_props == {"sq610-1": {"SystemMode": 4}}
    health = coordinator.gateway_diagnostics()
    assert health["raw_sq610_fetch_failures"] == 1


async def test_availability_history_tracks_missing_devices(hass: HomeAssistant) -> None:
    gateway = FakeGateway()
    coordinator = _coordinator(hass, gateway)

    await coordinator._async_update_data()
    gateway.climate_devices = {}
    gateway.raw_props = {}
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
