"""Diagnostics tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant

from custom_components.salus.coordinator import (
    SalusDataUpdateCoordinator,
    SalusRuntimeData,
)
from custom_components.salus.diagnostics import async_get_config_entry_diagnostics


def _sq610_device() -> SimpleNamespace:
    return SimpleNamespace(
        unique_id="sq610-1",
        available=True,
        name="Bedroom",
        model="SQ610RF",
        data={"UniID": "sq610-1"},
    )


class FakeGateway:
    def __init__(self) -> None:
        self.climate_devices = {"sq610-1": _sq610_device()}

    async def poll_status(self) -> None:
        return None

    def get_climate_devices(self) -> dict[str, Any]:
        return self.climate_devices

    def get_binary_sensor_devices(self) -> dict[str, Any]:
        return {}

    def get_switch_devices(self) -> dict[str, Any]:
        return {}

    def get_cover_devices(self) -> dict[str, Any]:
        return {}

    def get_sensor_devices(self) -> dict[str, Any]:
        return {}

    async def fetch_sq610_properties(
        self, device_ids: list[str]
    ) -> dict[str, dict[str, Any]]:
        return {
            device_ids[0]: {
                "OnlineStatus_i": 1,
                "LocalTemperature_x100": 2150,
                "HeatingSetpoint_x100": 2200,
                "SystemMode": 4,
            }
        }


async def test_diagnostics_redacts_token_and_reports_health(hass: HomeAssistant) -> None:
    gateway = FakeGateway()
    entry = MagicMock()
    entry.entry_id = "entry-1"
    entry.title = "Salus"
    entry.data = {CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"}
    entry.options = {}
    coordinator = SalusDataUpdateCoordinator(hass, entry, gateway)
    coordinator.gateway_id = "gateway-1"
    entry.runtime_data = SalusRuntimeData(
        gateway=gateway,
        coordinator=coordinator,
    )

    coordinator.data = await coordinator._async_update_data()
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["data"][CONF_HOST] == "192.0.2.10"
    assert diagnostics["entry"]["data"][CONF_TOKEN] == "**REDACTED**"
    assert diagnostics["runtime"]["loaded"] is True
    assert diagnostics["device_counts"]["climate"] == 1
    assert diagnostics["gateway"]["health"]["successful_updates"] == 1


async def test_diagnostics_handles_unloaded_entry(hass: HomeAssistant) -> None:
    entry = SimpleNamespace(
        entry_id="entry-1",
        title="Salus",
        data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["runtime"]["loaded"] is False
    assert diagnostics["entry"]["data"][CONF_TOKEN] == "**REDACTED**"
