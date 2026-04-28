"""Diagnostics tests."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from tests.ha_shim import install

install()

from homeassistant.const import CONF_HOST, CONF_TOKEN  # noqa: E402

from custom_components.salus.coordinator import (  # noqa: E402
    SalusDataUpdateCoordinator,
    SalusRuntimeData,
)
from custom_components.salus.diagnostics import (  # noqa: E402
    async_get_config_entry_diagnostics,
)


def _sq610_device() -> SimpleNamespace:
    return SimpleNamespace(
        unique_id="sq610-1",
        available=True,
        name="Bedroom",
        model="SQ610RF",
        data={"UniID": "sq610-1"},
    )


class FakeGateway:
    """Gateway fake for diagnostics tests."""

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
        self,
        device_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        return {
            device_ids[0]: {
                "OnlineStatus_i": 1,
                "LocalTemperature_x100": 2150,
                "HeatingSetpoint_x100": 2200,
                "SystemMode": 4,
            }
        }


class TestDiagnostics(unittest.IsolatedAsyncioTestCase):
    async def test_config_entry_diagnostics_redacts_and_reports_health(self) -> None:
        gateway = FakeGateway()
        hass = SimpleNamespace(data={})
        entry = SimpleNamespace(
            entry_id="entry-1",
            title="Salus",
            data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
        )
        coordinator = SalusDataUpdateCoordinator(hass, entry, gateway)
        coordinator.gateway_id = "gateway-1"
        entry.runtime_data = SalusRuntimeData(
            gateway=gateway,
            coordinator=coordinator,
        )

        coordinator.data = await coordinator._async_update_data()

        diagnostics = await async_get_config_entry_diagnostics(hass, entry)

        self.assertEqual("192.0.2.10", diagnostics["entry"]["data"][CONF_HOST])
        self.assertEqual("**REDACTED**", diagnostics["entry"]["data"][CONF_TOKEN])
        self.assertTrue(diagnostics["runtime"]["loaded"])
        self.assertEqual(1, diagnostics["device_counts"]["climate"])
        self.assertEqual(
            1,
            diagnostics["gateway"]["health"]["successful_updates"],
        )
        self.assertEqual(
            0,
            diagnostics["device_availability"]["sq610-1"][
                "consecutive_missed_refreshes"
            ],
        )
        self.assertEqual(
            2150,
            diagnostics["sq610"]["devices"]["sq610-1"]["support_fields"][
                "LocalTemperature_x100"
            ],
        )

    async def test_config_entry_diagnostics_handles_unloaded_entry(self) -> None:
        hass = SimpleNamespace(data={})
        entry = SimpleNamespace(
            entry_id="entry-1",
            title="Salus",
            data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
        )

        diagnostics = await async_get_config_entry_diagnostics(hass, entry)

        self.assertFalse(diagnostics["runtime"]["loaded"])
        self.assertEqual("**REDACTED**", diagnostics["entry"]["data"][CONF_TOKEN])


if __name__ == "__main__":
    unittest.main()
