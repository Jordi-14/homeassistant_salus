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

import custom_components.salus as salus_init
from custom_components.salus import (
    PLATFORMS,
    async_remove_config_entry_device,
    async_setup_entry,
)
from custom_components.salus.const import CONF_SCAN_INTERVAL, DOMAIN
from custom_components.salus.coordinator import SalusData, SalusRuntimeData
from tests.conftest import (
    FakeCoordinator,
    make_binary_sensor_device,
    make_climate_device,
    make_sensor_device,
    make_switch_device,
)


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
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
        state=ConfigEntryState.SETUP_IN_PROGRESS,
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})

    with (
        patch.object(salus_init, "IT600Gateway", FakeGateway),
        patch.object(
            hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock
        ) as mock_forward,
    ):
        result = await async_setup_entry(hass, entry)

    assert result is True
    mock_forward.assert_called_once_with(entry, PLATFORMS)
    assert FakeGateway.instances[0].kwargs[CONF_HOST] == "192.0.2.10"
    assert FakeGateway.instances[0].kwargs["session"] is not None
    assert not FakeGateway.instances[0].closed


async def test_setup_entry_uses_configured_scan_interval(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
        options={CONF_SCAN_INTERVAL: 45},
        state=ConfigEntryState.SETUP_IN_PROGRESS,
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})

    with (
        patch.object(salus_init, "IT600Gateway", FakeGateway),
        patch.object(
            hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock
        ),
    ):
        result = await async_setup_entry(hass, entry)

    assert result is True
    assert entry.runtime_data.coordinator.update_interval == timedelta(seconds=45)


# ---------------------------------------------------------------------------
# Device removal guard
# ---------------------------------------------------------------------------


def _salus_data(**collections: dict[str, Any]) -> SalusData:
    """Create a SalusData snapshot with empty defaults."""
    defaults: dict[str, dict[str, Any]] = {
        "climate_devices": {},
        "binary_sensor_devices": {},
        "switch_devices": {},
        "cover_devices": {},
        "sensor_devices": {},
    }
    defaults.update(collections)
    return SalusData(**defaults)


def _entry_with_data(data: SalusData) -> MockConfigEntry:
    """Create a config entry with fake runtime data around a snapshot."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
    )
    coordinator = FakeCoordinator(data=data)
    entry.runtime_data = SalusRuntimeData(
        gateway=coordinator.gateway, coordinator=coordinator
    )
    return entry


def _device_entry(*identifier_values: str, domain: str = DOMAIN) -> SimpleNamespace:
    """Create a device registry entry fake."""
    return SimpleNamespace(
        id="device-registry-id",
        identifiers={(domain, value) for value in identifier_values},
    )


async def test_remove_device_allowed_when_entry_not_loaded(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_TOKEN: "001E5E0D32906128"},
    )

    assert await async_remove_config_entry_device(
        hass, entry, _device_entry("climate-1")
    )


async def test_remove_device_refuses_live_device_and_allows_stale(
    hass: HomeAssistant,
) -> None:
    device = make_climate_device(unique_id="climate-1")
    entry = _entry_with_data(_salus_data(climate_devices={"climate-1": device}))

    assert not await async_remove_config_entry_device(
        hass, entry, _device_entry("climate-1")
    )
    assert await async_remove_config_entry_device(
        hass, entry, _device_entry("climate-gone")
    )


async def test_remove_device_refuses_gateway_device(hass: HomeAssistant) -> None:
    entry = _entry_with_data(_salus_data())

    # FakeCoordinator reports gateway_id "gateway-1".
    assert not await async_remove_config_entry_device(
        hass, entry, _device_entry("gateway-1")
    )


async def test_remove_device_compares_device_identity_not_entity_unique_id(
    hass: HomeAssistant,
) -> None:
    """A stale per-entity device stays deletable while its id is a live entity id.

    The sensor entity th-1_temperature groups under physical device th-1, so a
    leftover registry device identified by the entity's own unique_id must be
    removable even though that unique_id is still in the data snapshot.
    """
    sensor = make_sensor_device(
        unique_id="th-1_temperature",
        data={"UniID": "th-1", "Endpoint": 1},
    )
    entry = _entry_with_data(
        _salus_data(sensor_devices={"th-1_temperature": sensor})
    )

    assert await async_remove_config_entry_device(
        hass, entry, _device_entry("th-1_temperature")
    )
    assert not await async_remove_config_entry_device(
        hass, entry, _device_entry("th-1")
    )


async def test_remove_device_refuses_parent_referenced_by_child_entity(
    hass: HomeAssistant,
) -> None:
    child = make_binary_sensor_device(
        unique_id="th-9_window", parent_unique_id="th-9"
    )
    entry = _entry_with_data(
        _salus_data(binary_sensor_devices={"th-9_window": child})
    )

    assert not await async_remove_config_entry_device(
        hass, entry, _device_entry("th-9")
    )
    assert await async_remove_config_entry_device(
        hass, entry, _device_entry("th-9_window")
    )


async def test_remove_device_refuses_grouped_switch_physical_device(
    hass: HomeAssistant,
) -> None:
    switch = make_switch_device(
        unique_id="rs600_001_1",
        model="RS600",
        data={"UniID": "rs600_001", "Endpoint": 1},
    )
    entry = _entry_with_data(_salus_data(switch_devices={"rs600_001_1": switch}))

    assert not await async_remove_config_entry_device(
        hass, entry, _device_entry("rs600_001")
    )
    assert await async_remove_config_entry_device(
        hass, entry, _device_entry("rs600_001_1")
    )


async def test_remove_device_ignores_other_domain_identifiers(
    hass: HomeAssistant,
) -> None:
    device = make_climate_device(unique_id="climate-1")
    entry = _entry_with_data(_salus_data(climate_devices={"climate-1": device}))

    assert await async_remove_config_entry_device(
        hass, entry, _device_entry("climate-1", domain="other")
    )


async def test_remove_device_refuses_without_data_snapshot(
    hass: HomeAssistant,
) -> None:
    entry = _entry_with_data(_salus_data())
    entry.runtime_data.coordinator.data = None

    assert not await async_remove_config_entry_device(
        hass, entry, _device_entry("climate-gone")
    )


async def test_remove_device_refuses_on_unexpected_error(
    hass: HomeAssistant,
) -> None:
    entry = _entry_with_data(_salus_data())
    # A snapshot missing its collections raises inside the guard.
    entry.runtime_data.coordinator.data = SimpleNamespace()

    assert not await async_remove_config_entry_device(
        hass, entry, _device_entry("climate-gone")
    )
