"""Integration setup tests."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from tests.ha_shim import install

install()

from custom_components.salus import PLATFORMS, async_setup_entry, async_unload_entry  # noqa: E402
from custom_components.salus.const import DOMAIN  # noqa: E402
import custom_components.salus as salus_init  # noqa: E402
from homeassistant.const import CONF_HOST, CONF_TOKEN  # noqa: E402


class FakeGateway:
    """Gateway fake for setup tests."""

    instances: list[FakeGateway] = []
    poll_error: Exception | None = None

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.closed = False
        FakeGateway.instances.append(self)

    async def connect(self) -> str:
        return "gateway-1"

    async def poll_status(self) -> None:
        if FakeGateway.poll_error is not None:
            raise FakeGateway.poll_error
        return None

    async def close(self) -> None:
        self.closed = True

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
        self.unloaded_platforms: list[tuple[Any, tuple[Any, ...]]] = []
        self.forward_error: Exception | None = None
        self.unload_result = True

    async def async_forward_entry_setups(
        self,
        entry: Any,
        platforms: tuple[Any, ...],
    ) -> None:
        if self.forward_error is not None:
            raise self.forward_error
        self.forwarded_setups.append((entry, platforms))

    async def async_unload_platforms(
        self,
        entry: Any,
        platforms: tuple[Any, ...],
    ) -> bool:
        self.unloaded_platforms.append((entry, platforms))
        return self.unload_result


class TestSetupEntry(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        FakeGateway.instances = []
        FakeGateway.poll_error = None
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
        self.assertFalse(FakeGateway.instances[0].closed)

    async def test_unload_entry_closes_gateway_after_unloading_platforms(self) -> None:
        hass = SimpleNamespace(data={}, config_entries=FakeConfigEntries())
        entry = SimpleNamespace(
            entry_id="entry-1",
            data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
        )
        await async_setup_entry(hass, entry)

        result = await async_unload_entry(hass, entry)

        self.assertTrue(result)
        self.assertEqual([(entry, PLATFORMS)], hass.config_entries.unloaded_platforms)
        self.assertTrue(FakeGateway.instances[0].closed)
        self.assertNotIn(entry.entry_id, hass.data[DOMAIN])

    async def test_unload_entry_keeps_gateway_open_when_platform_unload_fails(
        self,
    ) -> None:
        hass = SimpleNamespace(data={}, config_entries=FakeConfigEntries())
        hass.config_entries.unload_result = False
        entry = SimpleNamespace(
            entry_id="entry-1",
            data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
        )
        await async_setup_entry(hass, entry)

        result = await async_unload_entry(hass, entry)

        self.assertFalse(result)
        self.assertFalse(FakeGateway.instances[0].closed)
        self.assertIn(entry.entry_id, hass.data[DOMAIN])

    async def test_setup_entry_closes_gateway_when_first_refresh_fails(self) -> None:
        FakeGateway.poll_error = RuntimeError("poll failed")
        hass = SimpleNamespace(data={}, config_entries=FakeConfigEntries())
        entry = SimpleNamespace(
            entry_id="entry-1",
            data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
        )

        with self.assertRaises(RuntimeError):
            await async_setup_entry(hass, entry)

        self.assertTrue(FakeGateway.instances[0].closed)
        self.assertIsNone(entry.runtime_data)
        self.assertNotIn(entry.entry_id, hass.data.get(DOMAIN, {}))

    async def test_setup_entry_cleans_runtime_data_when_platform_forwarding_fails(
        self,
    ) -> None:
        hass = SimpleNamespace(data={}, config_entries=FakeConfigEntries())
        hass.config_entries.forward_error = RuntimeError("forward failed")
        entry = SimpleNamespace(
            entry_id="entry-1",
            data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
        )

        with self.assertRaises(RuntimeError):
            await async_setup_entry(hass, entry)

        self.assertTrue(FakeGateway.instances[0].closed)
        self.assertIsNone(entry.runtime_data)
        self.assertNotIn(entry.entry_id, hass.data[DOMAIN])


if __name__ == "__main__":
    unittest.main()
