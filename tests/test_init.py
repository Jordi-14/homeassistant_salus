"""Integration setup tests."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.salus import PLATFORMS, async_setup_entry
from custom_components.salus.const import CONF_SCAN_INTERVAL, DOMAIN


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


@pytest.fixture(autouse=True)
def reset_fake_gateway():
    FakeGateway.instances = []
    FakeGateway.poll_error = None


async def test_setup_entry_forwards_platforms(hass: HomeAssistant) -> None:
    import custom_components.salus as salus_init

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
        state=ConfigEntryState.SETUP_IN_PROGRESS,
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})

    with patch.object(salus_init, "IT600Gateway", FakeGateway):
        with patch.object(
            hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock
        ) as mock_forward:
            result = await async_setup_entry(hass, entry)

    assert result is True
    mock_forward.assert_called_once_with(entry, PLATFORMS)
    assert FakeGateway.instances[0].kwargs[CONF_HOST] == "192.0.2.10"
    assert not FakeGateway.instances[0].closed


async def test_setup_entry_uses_configured_scan_interval(
    hass: HomeAssistant,
) -> None:
    import custom_components.salus as salus_init

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
        options={CONF_SCAN_INTERVAL: 45},
        state=ConfigEntryState.SETUP_IN_PROGRESS,
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})

    with patch.object(salus_init, "IT600Gateway", FakeGateway):
        with patch.object(
            hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock
        ):
            result = await async_setup_entry(hass, entry)

    assert result is True
    assert entry.runtime_data.coordinator.update_interval == timedelta(seconds=45)
