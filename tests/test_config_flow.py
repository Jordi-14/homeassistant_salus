"""Config flow tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from salus_it600.exceptions import (
    IT600AuthenticationError,
    IT600ConnectionError,
    IT600UnsupportedFirmwareError,
)

from custom_components.salus import config_flow
from custom_components.salus.const import (
    CONF_POLL_FAILURE_THRESHOLD,
    CONF_POST_COMMAND_REFRESH_DELAY,
    CONF_SCAN_INTERVAL,
    DOMAIN,
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


@pytest.fixture(autouse=True)
def reset_fake_gateway():
    FakeGateway.connect_error = None
    FakeGateway.instances = []


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Prevent actual setup after flow creates entry."""
    with patch(
        "custom_components.salus.async_setup_entry", return_value=True
    ):
        yield


async def test_user_step_success_creates_entry(hass: HomeAssistant) -> None:
    with patch.object(config_flow, "IT600Gateway", FakeGateway):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _input()
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Gateway"
    assert result["data"][CONF_HOST] == "192.0.2.10"
    assert result["data"][CONF_TOKEN] == "001E5E0D32906128"
    assert FakeGateway.instances[0].closed


async def test_user_step_connection_error_returns_form(hass: HomeAssistant) -> None:
    FakeGateway.connect_error = IT600ConnectionError("offline")
    with patch.object(config_flow, "IT600Gateway", FakeGateway):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _input()
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "connect_error"
    assert FakeGateway.instances[0].closed


async def test_user_step_auth_error_returns_form(hass: HomeAssistant) -> None:
    FakeGateway.connect_error = IT600AuthenticationError("bad euid")
    with patch.object(config_flow, "IT600Gateway", FakeGateway):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _input()
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "auth_error"
    assert FakeGateway.instances[0].closed


async def test_user_step_unsupported_firmware_returns_form(hass: HomeAssistant) -> None:
    FakeGateway.connect_error = IT600UnsupportedFirmwareError("protocol")
    with patch.object(config_flow, "IT600Gateway", FakeGateway):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], _input()
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "unsupported_firmware"
    assert FakeGateway.instances[0].closed


async def test_user_step_invalid_euid_returns_field_error(hass: HomeAssistant) -> None:
    with patch.object(config_flow, "IT600Gateway", FakeGateway):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.0.2.10",
                CONF_TOKEN: "too-short",
                CONF_NAME: "Gateway",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"][CONF_TOKEN] == "invalid_euid"
    assert FakeGateway.instances == []


def test_valid_euid_normalizes_case() -> None:
    assert config_flow._valid_euid("001e5e0d32906128") == "001E5E0D32906128"


def test_valid_euid_rejects_invalid_values() -> None:
    with pytest.raises(vol.Invalid):
        config_flow._valid_euid("not-valid")


async def test_options_flow_stores_scan_interval() -> None:
    flow = config_flow.SalusOptionsFlowHandler(SimpleNamespace(options={}))
    flow.flow_id = "test-flow"
    flow.handler = DOMAIN
    flow.context = {}

    result = await flow.async_step_init(
        {
            CONF_POLL_FAILURE_THRESHOLD: 5,
            CONF_SCAN_INTERVAL: 45,
            CONF_POST_COMMAND_REFRESH_DELAY: 4.5,
        }
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_POLL_FAILURE_THRESHOLD] == 5
    assert result["data"][CONF_SCAN_INTERVAL] == 45
    assert result["data"][CONF_POST_COMMAND_REFRESH_DELAY] == 4.5
