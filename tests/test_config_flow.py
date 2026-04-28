"""Config flow tests."""

from __future__ import annotations

import unittest
from typing import Any

from tests.ha_shim import install

install()

from custom_components.salus import config_flow  # noqa: E402
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN  # noqa: E402
from salus_it600.exceptions import (  # noqa: E402
    IT600AuthenticationError,
    IT600ConnectionError,
)


class FakeGateway:
    """Gateway fake for config-flow tests."""

    connect_error: Exception | None = None
    connected_unique_id = "AA:BB:CC:DD:EE:FF"
    instances: list[FakeGateway] = []

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.closed = False
        FakeGateway.instances.append(self)

    async def connect(self) -> str:
        if FakeGateway.connect_error is not None:
            raise FakeGateway.connect_error
        return FakeGateway.connected_unique_id

    async def close(self) -> None:
        self.closed = True


def _input() -> dict[str, str]:
    return {
        CONF_HOST: " 192.0.2.10 ",
        CONF_TOKEN: "001E5E0D32906128",
        CONF_NAME: "Gateway",
    }


class TestSalusFlowHandler(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        FakeGateway.connect_error = None
        FakeGateway.instances = []
        config_flow.IT600Gateway = FakeGateway

    async def test_user_step_success_creates_entry(self) -> None:
        flow = config_flow.SalusFlowHandler()

        result = await flow.async_step_user(_input())

        self.assertEqual("create_entry", result["type"])
        self.assertEqual("Gateway", result["title"])
        self.assertEqual("192.0.2.10", result["data"][CONF_HOST])
        self.assertEqual("001E5E0D32906128", result["data"][CONF_TOKEN])
        self.assertEqual(FakeGateway.connected_unique_id, result["data"]["mac"])
        self.assertTrue(FakeGateway.instances[0].closed)

    async def test_user_step_connection_error_returns_form_error(self) -> None:
        FakeGateway.connect_error = IT600ConnectionError("offline")
        flow = config_flow.SalusFlowHandler()

        result = await flow.async_step_user(_input())

        self.assertEqual("form", result["type"])
        self.assertEqual("connect_error", result["errors"]["base"])
        self.assertTrue(FakeGateway.instances[0].closed)

    async def test_user_step_auth_error_returns_form_error(self) -> None:
        FakeGateway.connect_error = IT600AuthenticationError("bad euid")
        flow = config_flow.SalusFlowHandler()

        result = await flow.async_step_user(_input())

        self.assertEqual("form", result["type"])
        self.assertEqual("auth_error", result["errors"]["base"])
        self.assertTrue(FakeGateway.instances[0].closed)

    def test_valid_euid_normalizes_case(self) -> None:
        self.assertEqual(
            "001E5E0D32906128",
            config_flow._valid_euid("001e5e0d32906128"),
        )

    def test_valid_euid_rejects_invalid_values(self) -> None:
        with self.assertRaises(config_flow.vol.Invalid):
            config_flow._valid_euid("not-valid")


if __name__ == "__main__":
    unittest.main()
