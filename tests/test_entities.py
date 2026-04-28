"""Command entity tests."""

from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace

from tests.ha_shim import install

install()

from custom_components.salus.coordinator import SalusData  # noqa: E402
from custom_components.salus.cover import SalusCover  # noqa: E402
from custom_components.salus.climate import SalusThermostat  # noqa: E402
from custom_components.salus.binary_sensor import SalusBinarySensor  # noqa: E402
from custom_components.salus.lock import SalusThermostatLock  # noqa: E402
from custom_components.salus.sensor import SalusSensor  # noqa: E402
from custom_components.salus.switch import SalusSwitch  # noqa: E402
from custom_components.salus.const import DOMAIN  # noqa: E402


class FakeGateway:
    """Gateway fake for command entity tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int | None]] = []

    async def turn_on_switch_device(self, device_id: str) -> None:
        self.calls.append(("turn_on_switch", device_id, None))

    async def turn_off_switch_device(self, device_id: str) -> None:
        self.calls.append(("turn_off_switch", device_id, None))

    async def open_cover(self, device_id: str) -> None:
        self.calls.append(("open_cover", device_id, None))

    async def close_cover(self, device_id: str) -> None:
        self.calls.append(("close_cover", device_id, None))

    async def set_cover_position(self, device_id: str, position: int) -> None:
        self.calls.append(("set_cover_position", device_id, position))

    async def set_climate_device_locked(self, device_id: str, locked: bool) -> None:
        self.calls.append(("set_climate_locked", device_id, int(locked)))


class FakeCoordinator:
    """Coordinator fake for command entity tests."""

    def __init__(self) -> None:
        self.gateway = FakeGateway()
        self.gateway_lock = asyncio.Lock()
        self.gateway_id = "gateway"
        self.refresh_requests = 0
        self.data = SalusData(
            climate_devices={
                "climate-1": SimpleNamespace(
                    available=True,
                    unique_id="climate-1",
                    name="Thermostat",
                    manufacturer="SALUS",
                    model="SQ610RF",
                    sw_version=None,
                    locked=False,
                )
            },
            binary_sensor_devices={
                "climate-1_problem": SimpleNamespace(
                    available=True,
                    unique_id="climate-1_problem",
                    name="Thermostat Problem",
                    manufacturer="SALUS",
                    model="SQ610RF",
                    sw_version=None,
                    is_on=True,
                    device_class="problem",
                    parent_unique_id="climate-1",
                    entity_category="diagnostic",
                    extra_state_attributes={"errors": ["Floor sensor overheating"]},
                )
            },
            switch_devices={
                "switch-1": SimpleNamespace(
                    available=True,
                    unique_id="switch-1",
                    name="Switch",
                    manufacturer="SALUS",
                    model="SPE600",
                    sw_version=None,
                    device_class="outlet",
                    is_on=False,
                )
            },
            cover_devices={
                "cover-1": SimpleNamespace(
                    available=True,
                    unique_id="cover-1",
                    name="Cover",
                    manufacturer="SALUS",
                    model="RS600",
                    sw_version=None,
                    supported_features=7,
                    device_class=None,
                    current_cover_position=10,
                    is_opening=False,
                    is_closing=False,
                    is_closed=False,
                )
            },
            sensor_devices={
                "switch-1_power": SimpleNamespace(
                    available=True,
                    unique_id="switch-1_power",
                    name="Switch Power",
                    manufacturer="SALUS",
                    model="SPE600",
                    sw_version=None,
                    state=42,
                    unit_of_measurement="W",
                    device_class="power",
                    parent_unique_id="switch-1",
                    entity_category=None,
                ),
                "climate-1_battery": SimpleNamespace(
                    available=True,
                    unique_id="climate-1_battery",
                    name="Thermostat Battery",
                    manufacturer="SALUS",
                    model="SQ610RF",
                    sw_version=None,
                    state=75,
                    unit_of_measurement="%",
                    device_class="battery",
                    parent_unique_id="climate-1",
                    entity_category="diagnostic",
                ),
            },
            raw_climate_props={},
        )

    async def async_request_debounced_refresh(self) -> None:
        self.refresh_requests += 1


class TestCommandEntities(unittest.IsolatedAsyncioTestCase):
    async def test_climate_turn_on_off_backwards_compatibility_is_disabled(self) -> None:
        self.assertFalse(SalusThermostat._enable_turn_on_off_backwards_compatibility)

    async def test_switch_commands_write_gateway_and_debounce_refresh(self) -> None:
        coordinator = FakeCoordinator()
        entity = SalusSwitch(coordinator, "switch-1")

        await entity.async_turn_on()
        await entity.async_turn_off()

        self.assertEqual(
            [
                ("turn_on_switch", "switch-1", None),
                ("turn_off_switch", "switch-1", None),
            ],
            coordinator.gateway.calls,
        )
        self.assertEqual(2, coordinator.refresh_requests)

    async def test_cover_commands_write_gateway_and_debounce_refresh(self) -> None:
        coordinator = FakeCoordinator()
        entity = SalusCover(coordinator, "cover-1")

        await entity.async_open_cover()
        await entity.async_close_cover()
        await entity.async_set_cover_position(position=42)

        self.assertEqual(
            [
                ("open_cover", "cover-1", None),
                ("close_cover", "cover-1", None),
                ("set_cover_position", "cover-1", 42),
            ],
            coordinator.gateway.calls,
        )
        self.assertEqual(3, coordinator.refresh_requests)

    async def test_sensor_child_entity_uses_parent_device_and_category(self) -> None:
        coordinator = FakeCoordinator()
        entity = SalusSensor(coordinator, "climate-1_battery")

        self.assertEqual(75, entity.native_value)
        self.assertEqual("battery", entity.device_class)
        self.assertEqual("diagnostic", entity.entity_category)
        self.assertEqual(
            {"identifiers": {(DOMAIN, "climate-1")}},
            entity.device_info,
        )

    async def test_binary_child_entity_uses_parent_device_and_attributes(self) -> None:
        coordinator = FakeCoordinator()
        entity = SalusBinarySensor(coordinator, "climate-1_problem")

        self.assertTrue(entity.is_on)
        self.assertEqual("problem", entity.device_class)
        self.assertEqual("diagnostic", entity.entity_category)
        self.assertEqual(
            {"errors": ["Floor sensor overheating"]},
            entity.extra_state_attributes,
        )
        self.assertEqual(
            {"identifiers": {(DOMAIN, "climate-1")}},
            entity.device_info,
        )

    async def test_lock_commands_write_gateway_and_debounce_refresh(self) -> None:
        coordinator = FakeCoordinator()
        entity = SalusThermostatLock(coordinator, "climate-1")

        self.assertFalse(entity.is_locked)
        self.assertEqual("climate-1_lock", entity._attr_unique_id)
        await entity.async_lock()
        await entity.async_unlock()

        self.assertEqual(
            [
                ("set_climate_locked", "climate-1", 1),
                ("set_climate_locked", "climate-1", 0),
            ],
            coordinator.gateway.calls,
        )
        self.assertEqual(2, coordinator.refresh_requests)


if __name__ == "__main__":
    unittest.main()
