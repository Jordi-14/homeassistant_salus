"""Integration setup tests."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from tests.ha_shim import install

install()

from custom_components.salus import PLATFORMS, async_setup_entry  # noqa: E402
import custom_components.salus as salus_init  # noqa: E402
from homeassistant.const import CONF_HOST, CONF_TOKEN  # noqa: E402


class FakeGateway:
    """Gateway fake for setup tests."""

    instances: list[FakeGateway] = []

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        FakeGateway.instances.append(self)

    async def connect(self) -> str:
        return "gateway-1"

    async def poll_status(self) -> None:
        return None

    def get_gateway_device(self) -> SimpleNamespace:
        return SimpleNamespace(
            unique_id="gateway-1",
            manufacturer="SALUS",
            name="Gateway",
            model="UGE600",
            sw_version="1.0",
        )

    def get_climate_devices(self) -> dict[str, Any]:
        return {}

    def get_binary_sensor_devices(self) -> dict[str, Any]:
        return {}

    def get_switch_devices(self) -> dict[str, Any]:
        return {}

    def get_cover_devices(self) -> dict[str, Any]:
        return {}

    def get_sensor_devices(self) -> dict[str, Any]:
        return {}


class FakeConfigEntries:
    """Config entries fake that records awaited setup forwarding."""

    def __init__(self) -> None:
        self.forwarded_setups: list[tuple[Any, tuple[Any, ...]]] = []

    async def async_forward_entry_setups(
        self,
        entry: Any,
        platforms: tuple[Any, ...],
    ) -> None:
        self.forwarded_setups.append((entry, platforms))


class TestSetupEntry(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        FakeGateway.instances = []
        salus_init.IT600Gateway = FakeGateway

    async def test_setup_entry_awaits_forward_entry_setups(self) -> None:
        hass = SimpleNamespace(data={}, config_entries=FakeConfigEntries())
        entry = SimpleNamespace(
            entry_id="entry-1",
            data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
        )

        result = await async_setup_entry(hass, entry)

        self.assertTrue(result)
        self.assertEqual([(entry, PLATFORMS)], hass.config_entries.forwarded_setups)
        self.assertEqual("192.0.2.10", FakeGateway.instances[0].kwargs[CONF_HOST])


if __name__ == "__main__":
    unittest.main()
