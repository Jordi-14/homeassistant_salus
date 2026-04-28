"""Coordinator tests."""

from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from typing import Any

from tests.ha_shim import ConfigEntryAuthFailed, UpdateFailed, install

install()

from custom_components.salus.coordinator import (  # noqa: E402
    SalusData,
    SalusDataUpdateCoordinator,
)
from salus_it600.exceptions import (  # noqa: E402
    IT600AuthenticationError,
    IT600ConnectionError,
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
        self,
        device_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        self.raw_fetch_ids = device_ids
        if self.raw_error is not None:
            raise self.raw_error
        return self.raw_props


def _coordinator(gateway: FakeGateway) -> SalusDataUpdateCoordinator:
    return SalusDataUpdateCoordinator(
        hass=object(),
        config_entry=object(),
        gateway=gateway,
    )


class TestSalusDataUpdateCoordinator(unittest.IsolatedAsyncioTestCase):
    async def test_update_data_populates_snapshot_and_fetches_sq610_props(self) -> None:
        gateway = FakeGateway()
        coordinator = _coordinator(gateway)

        data = await coordinator._async_update_data()

        self.assertEqual(
            {"sq610-1": gateway.climate_devices["sq610-1"]},
            data.climate_devices,
        )
        self.assertEqual(
            {"sq610-1": {"SystemMode": 3, "OnlineStatus_i": 1}},
            data.raw_climate_props,
        )
        self.assertEqual(["sq610-1"], gateway.raw_fetch_ids)

        gateway_health = coordinator.gateway_diagnostics()
        self.assertEqual(1, gateway_health["successful_updates"])
        self.assertEqual(0, gateway_health["consecutive_update_failures"])
        self.assertEqual(1, gateway_health["raw_sq610_fetch_successes"])

        device_health = coordinator.device_availability_diagnostics()["sq610-1"]
        self.assertTrue(device_health["available"])
        self.assertEqual("climate", device_health["platform"])
        self.assertEqual(1, device_health["raw_online_status"])
        self.assertEqual("raw_sq610_props", device_health["raw_online_status_source"])
        self.assertEqual(0, device_health["consecutive_missed_refreshes"])

    async def test_update_data_maps_auth_failure(self) -> None:
        gateway = FakeGateway()
        gateway.poll_error = IT600AuthenticationError("bad euid")
        coordinator = _coordinator(gateway)

        with self.assertRaises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

        self.assertEqual(
            1,
            coordinator.gateway_diagnostics()["consecutive_update_failures"],
        )

    async def test_update_data_maps_connection_failure(self) -> None:
        gateway = FakeGateway()
        gateway.poll_error = IT600ConnectionError("offline")
        coordinator = _coordinator(gateway)

        with self.assertRaises(UpdateFailed):
            await coordinator._async_update_data()

        self.assertIn(
            "IT600ConnectionError: offline",
            coordinator.gateway_diagnostics()["last_update_error"],
        )

    async def test_raw_sq610_failure_uses_last_known_values(self) -> None:
        gateway = FakeGateway()
        gateway.raw_error = IT600ConnectionError("offline")
        coordinator = _coordinator(gateway)
        coordinator.data = SalusData(
            climate_devices={},
            binary_sensor_devices={},
            switch_devices={},
            cover_devices={},
            sensor_devices={},
            raw_climate_props={"sq610-1": {"SystemMode": 4}},
        )

        with self.assertLogs("custom_components.salus.coordinator", level="WARNING"):
            raw_props = await coordinator._async_fetch_raw_climate_props(
                gateway.climate_devices,
            )

        self.assertEqual({"sq610-1": {"SystemMode": 4}}, raw_props)
        gateway_health = coordinator.gateway_diagnostics()
        self.assertEqual(1, gateway_health["raw_sq610_fetch_failures"])
        self.assertIn(
            "IT600ConnectionError: offline",
            gateway_health["last_raw_sq610_fetch_error"],
        )

    async def test_availability_history_tracks_missing_devices(self) -> None:
        gateway = FakeGateway()
        coordinator = _coordinator(gateway)

        await coordinator._async_update_data()
        gateway.climate_devices = {}
        gateway.raw_props = {}
        await coordinator._async_update_data()

        device_health = coordinator.device_availability_diagnostics()["sq610-1"]
        self.assertFalse(device_health["available"])
        self.assertEqual("missing_from_snapshot", device_health["raw_online_status_source"])
        self.assertEqual(1, device_health["consecutive_missed_refreshes"])

    async def test_debounced_refresh_coalesces_rapid_requests(self) -> None:
        coordinator = _coordinator(FakeGateway())
        coordinator._refresh_debounce_delay = 0

        await coordinator.async_request_debounced_refresh()
        await coordinator.async_request_debounced_refresh()
        await coordinator.async_request_debounced_refresh()

        self.assertIsNotNone(coordinator._debounced_refresh_task)
        await coordinator._debounced_refresh_task
        await asyncio.sleep(0)

        self.assertEqual(1, coordinator.refresh_count)
        self.assertIsNone(coordinator._debounced_refresh_task)

    async def test_cancel_debounced_refresh_clears_pending_task(self) -> None:
        coordinator = _coordinator(FakeGateway())
        coordinator._refresh_debounce_delay = 60

        await coordinator.async_request_debounced_refresh()
        self.assertIsNotNone(coordinator._debounced_refresh_task)

        coordinator.async_cancel_debounced_refresh()
        await asyncio.sleep(0)

        self.assertIsNone(coordinator._debounced_refresh_task)
        self.assertEqual(0, coordinator.refresh_count)


if __name__ == "__main__":
    unittest.main()
