"""Config flow tests."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from tests.ha_shim import install

install()

from custom_components.salus import config_flow  # noqa: E402
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN  # noqa: E402
from salus_it600.exceptions import (  # noqa: E402
    IT600AuthenticationError,
    IT600ConnectionError,
    IT600UnsupportedFirmwareError,
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


def _entry() -> SimpleNamespace:
    return SimpleNamespace(
        data={
            CONF_HOST: "192.0.2.10",
            CONF_TOKEN: "001E5E0D32906128",
            config_flow.CONF_MAC: FakeGateway.connected_unique_id,
        },
        options={},
    )


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
        self.assertEqual(
            FakeGateway.connected_unique_id,
            result["data"][config_flow.CONF_MAC],
        )
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

    async def test_user_step_unsupported_firmware_returns_form_error(self) -> None:
        FakeGateway.connect_error = IT600UnsupportedFirmwareError("protocol")
        flow = config_flow.SalusFlowHandler()

        result = await flow.async_step_user(_input())

        self.assertEqual("form", result["type"])
        self.assertEqual("unsupported_firmware", result["errors"]["base"])
        self.assertTrue(FakeGateway.instances[0].closed)

    def test_valid_euid_normalizes_case(self) -> None:
        self.assertEqual(
            "001E5E0D32906128",
            config_flow._valid_euid("001e5e0d32906128"),
        )

    def test_valid_euid_rejects_invalid_values(self) -> None:
        with self.assertRaises(config_flow.vol.Invalid):
            config_flow._valid_euid("not-valid")

    def test_get_options_flow_returns_options_handler(self) -> None:
        config_entry = SimpleNamespace(options={})

        flow = config_flow.SalusFlowHandler.async_get_options_flow(config_entry)

        self.assertIsInstance(flow, config_flow.SalusOptionsFlowHandler)
        self.assertIs(config_entry, flow._config_entry)

    async def test_options_flow_shows_form(self) -> None:
        flow = config_flow.SalusOptionsFlowHandler(
            SimpleNamespace(
                options={
                    config_flow.CONF_POLL_FAILURE_THRESHOLD: 5,
                    config_flow.CONF_POST_COMMAND_REFRESH_DELAY: 4.0,
                }
            )
        )

        result = await flow.async_step_init()

        self.assertEqual("form", result["type"])
        self.assertEqual("init", result["step_id"])
        schema = result["data_schema"].schema
        self.assertIsInstance(
            schema[config_flow.CONF_POLL_FAILURE_THRESHOLD],
            config_flow.selector.NumberSelector,
        )
        self.assertEqual(
            config_flow.selector.NumberSelectorMode.BOX,
            schema[config_flow.CONF_POLL_FAILURE_THRESHOLD].config["mode"],
        )
        self.assertIsInstance(
            schema[config_flow.CONF_POST_COMMAND_REFRESH_DELAY],
            config_flow.selector.NumberSelector,
        )
        self.assertEqual(
            "s",
            schema[config_flow.CONF_POST_COMMAND_REFRESH_DELAY].config[
                "unit_of_measurement"
            ],
        )

    async def test_options_flow_saves_refresh_options(self) -> None:
        flow = config_flow.SalusOptionsFlowHandler(SimpleNamespace(options={}))

        result = await flow.async_step_init(
            {
                config_flow.CONF_POLL_FAILURE_THRESHOLD: 7,
                config_flow.CONF_POST_COMMAND_REFRESH_DELAY: 4.5,
            }
        )

        self.assertEqual("create_entry", result["type"])
        self.assertEqual(
            {
                config_flow.CONF_POLL_FAILURE_THRESHOLD: 7,
                config_flow.CONF_POST_COMMAND_REFRESH_DELAY: 4.5,
            },
            result["data"],
        )

    async def test_user_step_invalid_euid_returns_field_error(self) -> None:
        flow = config_flow.SalusFlowHandler()

        result = await flow.async_step_user(
            {
                CONF_HOST: "192.0.2.10",
                CONF_TOKEN: "too-short",
                CONF_NAME: "Gateway",
            }
        )

        self.assertEqual("form", result["type"])
        self.assertEqual("invalid_euid", result["errors"][CONF_TOKEN])
        self.assertEqual([], FakeGateway.instances)

    async def test_reconfigure_updates_existing_entry(self) -> None:
        entry = _entry()
        flow = config_flow.SalusFlowHandler()
        flow.reconfigure_entry = entry

        result = await flow.async_step_reconfigure(
            {
                CONF_HOST: " 192.0.2.11 ",
                CONF_TOKEN: "001e5e0d32906128",
            }
        )

        self.assertEqual("abort", result["type"])
        self.assertEqual("reconfigure_successful", result["reason"])
        self.assertEqual("192.0.2.11", entry.data[CONF_HOST])
        self.assertEqual("001E5E0D32906128", entry.data[CONF_TOKEN])
        self.assertEqual(FakeGateway.connected_unique_id, entry.data[config_flow.CONF_MAC])
        self.assertTrue(FakeGateway.instances[0].closed)

    async def test_reconfigure_returns_connection_error(self) -> None:
        FakeGateway.connect_error = IT600ConnectionError("offline")
        entry = _entry()
        flow = config_flow.SalusFlowHandler()
        flow.reconfigure_entry = entry

        result = await flow.async_step_reconfigure(
            {
                CONF_HOST: "192.0.2.11",
                CONF_TOKEN: "001E5E0D32906128",
            }
        )

        self.assertEqual("form", result["type"])
        self.assertEqual("reconfigure", result["step_id"])
        self.assertEqual("connect_error", result["errors"]["base"])
        self.assertEqual("192.0.2.10", entry.data[CONF_HOST])
        self.assertTrue(FakeGateway.instances[0].closed)

    async def test_reconfigure_invalid_euid_returns_field_error(self) -> None:
        entry = _entry()
        flow = config_flow.SalusFlowHandler()
        flow.reconfigure_entry = entry

        result = await flow.async_step_reconfigure(
            {
                CONF_HOST: "192.0.2.11",
                CONF_TOKEN: "invalid",
            }
        )

        self.assertEqual("form", result["type"])
        self.assertEqual("reconfigure", result["step_id"])
        self.assertEqual("invalid_euid", result["errors"][CONF_TOKEN])
        self.assertEqual("192.0.2.10", entry.data[CONF_HOST])
        self.assertEqual([], FakeGateway.instances)

    async def test_reauth_updates_existing_entry(self) -> None:
        entry = _entry()
        flow = config_flow.SalusFlowHandler()
        flow.reauth_entry = entry

        result = await flow.async_step_reauth_confirm(
            {
                CONF_HOST: "192.0.2.10",
                CONF_TOKEN: "0000000000000000",
            }
        )

        self.assertEqual("abort", result["type"])
        self.assertEqual("reconfigure_successful", result["reason"])
        self.assertEqual("0000000000000000", entry.data[CONF_TOKEN])
        self.assertEqual(FakeGateway.connected_unique_id, entry.data[config_flow.CONF_MAC])
        self.assertTrue(FakeGateway.instances[0].closed)


if __name__ == "__main__":
    unittest.main()
