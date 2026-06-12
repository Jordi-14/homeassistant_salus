"""Diagnostics tests."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

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
        current_temperature=21.5,
        current_humidity=45.5,
        target_temperature=22.0,
        min_temp=5.0,
        max_temp=35.0,
        online_status=1,
        hold_type=2,
        system_mode=4,
        running_state=0,
        heating_setpoint=22.0,
        cooling_setpoint=None,
        min_heat_temp=5.0,
        max_heat_temp=35.0,
        min_cool_temp=None,
        max_cool_temp=None,
        heating_control=1,
        cooling_control=0,
        supports_cooling=True,
        cooling_capability_source="cooling_control",
        diagnostic_fields={
            "OnlineStatus_i": 1,
            "CoolingControl": 0,
            "SystemMode": 4,
            "LockKey": 1,
            "LockKey_a": 1,
            "HeatingSetpoint_x100": 2200,
            "SunnySetpoint_x100": 4550,
        },
    )


def _fc600_device() -> SimpleNamespace:
    return SimpleNamespace(
        unique_id="fc600-1",
        available=True,
        name="Fan Coil",
        model="FC600",
        data={"UniID": "fc600-1"},
        current_temperature=20.5,
        current_humidity=None,
        target_temperature=23.0,
        min_temp=16.0,
        max_temp=32.0,
        hvac_mode="cool",
        hvac_action="cooling",
        hvac_modes=("heat", "cool", "auto"),
        preset_mode="Eco",
        preset_modes=("Off", "Permanent Hold", "Eco", "Follow Schedule"),
        fan_mode="High",
        fan_modes=("Auto", "High", "Medium", "Low", "Off"),
        online_status=1,
        hold_type=10,
        system_mode=3,
        running_state=66,
        heating_setpoint=21.0,
        cooling_setpoint=23.0,
        min_heat_temp=5.0,
        max_heat_temp=40.0,
        min_cool_temp=16.0,
        max_cool_temp=32.0,
        heating_control=1,
        cooling_control=1,
        supports_cooling=True,
        supports_fan=True,
        supports_heat=True,
        cooling_capability_source="known_model",
        diagnostic_fields={
            "OnlineStatus_i": 1,
            "ModelIdentifier_i": "FC600",
            "SystemMode": 3,
            "RunningState": 66,
            "HoldType": 10,
            "CoolingSetpoint_x100": 2300,
        },
    )


class FakeGateway:
    def __init__(self) -> None:
        self.climate_devices = {
            "fc600-1": _fc600_device(),
            "sq610-1": _sq610_device(),
        }

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
    assert "001E5E0D32906128" not in json.dumps(diagnostics)
    assert diagnostics["runtime"]["loaded"] is True
    assert diagnostics["device_counts"]["climate"] == 2
    assert diagnostics["gateway"]["health"]["successful_updates"] == 1
    assert diagnostics["climate"]["devices"]["sq610-1"]["support_fields"][
        "LockKey"
    ] == 1
    assert diagnostics["climate"]["devices"]["sq610-1"]["support_fields"][
        "LockKey_a"
    ] == 1
    assert diagnostics["climate"]["devices"]["sq610-1"]["support_fields"][
        "CoolingControl"
    ] == 0
    assert diagnostics["climate"]["devices"]["sq610-1"]["support_fields"][
        "HeatingSetpoint_x100"
    ] == 2200
    assert diagnostics["climate"]["devices"]["sq610-1"]["support_fields"][
        "SunnySetpoint_x100"
    ] == 4550
    assert diagnostics["climate"]["devices"]["sq610-1"]["normalized_fields"][
        "current_humidity"
    ] == 45.5
    assert diagnostics["climate"]["devices"]["sq610-1"]["normalized_fields"][
        "supports_cooling"
    ] is True
    assert diagnostics["climate"]["devices"]["fc600-1"]["support_fields"][
        "CoolingSetpoint_x100"
    ] == 2300
    assert diagnostics["climate"]["devices"]["fc600-1"]["normalized_fields"][
        "supports_fan"
    ] is True


async def test_diagnostics_handles_unloaded_entry(hass: HomeAssistant) -> None:
    entry = SimpleNamespace(
        entry_id="entry-1",
        title="Salus",
        data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["runtime"]["loaded"] is False
    assert diagnostics["entry"]["data"][CONF_TOKEN] == "**REDACTED**"
