"""Coordinator tests using a small Home Assistant compatibility shim."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

CLIENT_ROOT = Path(__file__).resolve().parents[2] / "salus-it600-client"
sys.path.insert(0, str(CLIENT_ROOT))


class ConfigEntryAuthFailed(Exception):
    """Test stand-in for Home Assistant's ConfigEntryAuthFailed."""


class ConfigEntryNotReady(Exception):
    """Test stand-in for Home Assistant's ConfigEntryNotReady."""


class UpdateFailed(Exception):
    """Test stand-in for Home Assistant's UpdateFailed."""


class DataUpdateCoordinator:
    """Minimal DataUpdateCoordinator stand-in for coordinator unit tests."""

    def __class_getitem__(cls, _item: Any) -> type[DataUpdateCoordinator]:
        return cls

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self.data = None


class Platform:
    """Minimal Home Assistant Platform enum stand-in."""

    CLIMATE = "climate"
    BINARY_SENSOR = "binary_sensor"
    SWITCH = "switch"
    COVER = "cover"
    SENSOR = "sensor"


def _install_homeassistant_shim() -> None:
    homeassistant = types.ModuleType("homeassistant")
    config_entries = types.ModuleType("homeassistant.config_entries")
    core = types.ModuleType("homeassistant.core")
    const = types.ModuleType("homeassistant.const")
    exceptions = types.ModuleType("homeassistant.exceptions")
    helpers = types.ModuleType("homeassistant.helpers")
    device_registry = types.ModuleType("homeassistant.helpers.device_registry")
    update_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")

    config_entries.ConfigEntry = type("ConfigEntry", (), {})
    core.HomeAssistant = type("HomeAssistant", (), {})
    const.CONF_HOST = "host"
    const.CONF_TOKEN = "token"
    const.Platform = Platform
    exceptions.ConfigEntryAuthFailed = ConfigEntryAuthFailed
    exceptions.ConfigEntryNotReady = ConfigEntryNotReady
    device_registry.CONNECTION_NETWORK_MAC = "mac"
    device_registry.async_get = lambda _hass: SimpleNamespace(
        async_get_or_create=lambda **_kwargs: None
    )
    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    update_coordinator.UpdateFailed = UpdateFailed

    sys.modules.setdefault("homeassistant", homeassistant)
    sys.modules.setdefault("homeassistant.config_entries", config_entries)
    sys.modules.setdefault("homeassistant.core", core)
    sys.modules.setdefault("homeassistant.const", const)
    sys.modules.setdefault("homeassistant.exceptions", exceptions)
    sys.modules.setdefault("homeassistant.helpers", helpers)
    sys.modules.setdefault("homeassistant.helpers.device_registry", device_registry)
    sys.modules.setdefault(
        "homeassistant.helpers.update_coordinator",
        update_coordinator,
    )


_install_homeassistant_shim()

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
        self.raw_props = {"sq610-1": {"SystemMode": 3}}
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

        self.assertEqual({"sq610-1": gateway.climate_devices["sq610-1"]}, data.climate_devices)
        self.assertEqual({"sq610-1": {"SystemMode": 3}}, data.raw_climate_props)
        self.assertEqual(["sq610-1"], gateway.raw_fetch_ids)

    async def test_update_data_maps_auth_failure(self) -> None:
        gateway = FakeGateway()
        gateway.poll_error = IT600AuthenticationError("bad euid")
        coordinator = _coordinator(gateway)

        with self.assertRaises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    async def test_update_data_maps_connection_failure(self) -> None:
        gateway = FakeGateway()
        gateway.poll_error = IT600ConnectionError("offline")
        coordinator = _coordinator(gateway)

        with self.assertRaises(UpdateFailed):
            await coordinator._async_update_data()

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


if __name__ == "__main__":
    unittest.main()
