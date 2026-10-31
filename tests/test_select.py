"""Opt-in comfort control returns on acknowledgement and confirms through polls."""

import asyncio
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from salus_it600.exceptions import IT600ConnectionError

from custom_components.salus.select import (
    SalusComfortWarmFloorSelect,
    async_setup_entry,
)
from tests.conftest import FakeCoordinator, make_climate_device


@pytest.fixture(autouse=True)
def floor_client_api(monkeypatch):
    """Mock the future optional client API while testing with released 0.7.0.

    A deliberately different window catches an integration-local timeout value.
    Select lifecycle is tested here; client encoding and transport have their own tests.
    """
    module = ModuleType("salus_it600.comfort_warm_floor")
    module.COMFORT_PENDING_SECONDS = 137.0
    monkeypatch.setitem(sys.modules, module.__name__, module)
    return module


def setup_select():
    """Create a supported device with an acknowledgement-only mock gateway."""
    device = make_climate_device(model="SQ610RFNH")
    device.advanced_settings = SimpleNamespace(comfort_warm_floor=0)
    device.supports_comfort_warm_floor = True
    coordinator = FakeCoordinator()
    coordinator.data.climate_devices[device.unique_id] = device
    coordinator.gateway.set_climate_device_comfort_warm_floor = AsyncMock()
    return (
        SalusComfortWarmFloorSelect(coordinator, device.unique_id),
        coordinator,
        device,
    )


def test_floor_select_is_opt_in_and_has_no_controller_attributes():
    """Expose an opt-in select without custom controller state."""
    entity, _, _ = setup_select()
    assert entity.entity_registry_enabled_default is False
    assert entity.translation_key == "comfort_warm_floor"
    assert entity.extra_state_attributes is None


async def test_ack_returns_requested_level_as_assumed_until_poll_confirms():
    """Release the gateway lock after acknowledgement and confirm from polls."""
    entity, coordinator, device = setup_select()
    await entity.async_select_option("level_3")
    coordinator.gateway.set_climate_device_comfort_warm_floor.assert_awaited_once_with(
        device.unique_id, 3
    )
    assert entity.current_option == "level_3"
    assert entity.assumed_state
    assert not coordinator.gateway_lock.locked()
    async with asyncio.timeout(0.1):
        async with coordinator.gateway_lock:
            pass  # Other polls and commands can proceed during confirmation.
    device.advanced_settings.comfort_warm_floor = 3
    assert entity.current_option == "level_3"
    assert not entity.assumed_state
    assert coordinator.refresh_requests == 1


async def test_pending_window_is_longer_than_thirty_seconds_but_bounded(
    floor_client_api,
):
    """Use the client window and discard expired optimistic levels."""
    entity, _, _ = setup_select()
    now = [0]
    entity._loop_time = lambda: now[0]
    await entity.async_select_option("level_1")
    now[0] = 60
    assert entity.current_option == "level_1" and entity.assumed_state
    now[0] = floor_client_api.COMFORT_PENDING_SECONDS
    assert entity.current_option == "off" and not entity.assumed_state


async def test_failed_write_clears_optimistic_state_and_does_not_replay():
    """Clear a failed request without retrying it."""
    entity, coordinator, _ = setup_select()
    coordinator.gateway.set_climate_device_comfort_warm_floor.side_effect = (
        IT600ConnectionError("lost")
    )
    with pytest.raises(HomeAssistantError):
        await entity.async_select_option("level_1")
    assert entity.current_option == "off"
    assert not entity.assumed_state
    assert coordinator.gateway.set_climate_device_comfort_warm_floor.await_count == 1


async def test_second_choice_preserves_first_pending_value():
    """Reject a second choice before it can replace the first pending request."""
    entity, coordinator, _ = setup_select()
    await entity.async_select_option("level_1")
    first = entity._pending_state["current_option"]
    with pytest.raises(ServiceValidationError, match="still pending"):
        await entity.async_select_option("level_3")
    assert entity.current_option == "level_1"
    assert entity.assumed_state
    assert entity._pending_state["current_option"] is first
    assert coordinator.gateway.set_climate_device_comfort_warm_floor.await_count == 1


async def test_confirmed_first_choice_allows_a_second_choice():
    """Reconcile device confirmation before deciding whether a new write is allowed."""
    entity, coordinator, device = setup_select()
    await entity.async_select_option("level_1")
    device.advanced_settings.comfort_warm_floor = 1
    await entity.async_select_option("level_3")
    assert entity.current_option == "level_3"
    assert entity.assumed_state
    assert coordinator.gateway.set_climate_device_comfort_warm_floor.await_count == 2


async def test_expired_choice_allows_a_fresh_request(floor_client_api):
    """Clear expiry through the explicit pending helper without reading the property."""
    entity, coordinator, _ = setup_select()
    now = [0]
    entity._loop_time = lambda: now[0]
    await entity.async_select_option("level_1")
    now[0] = floor_client_api.COMFORT_PENDING_SECONDS
    await entity.async_select_option("level_2")
    assert entity.current_option == "level_2"
    assert entity.assumed_state
    assert coordinator.gateway.set_climate_device_comfort_warm_floor.await_count == 2


async def test_platform_only_discovers_client_supported_profiles():
    """Discover only flagged devices, including devices becoming supported later."""
    _, coordinator, supported = setup_select()
    unsupported = make_climate_device(unique_id="unsupported")
    unsupported.supports_comfort_warm_floor = False
    legacy = make_climate_device(unique_id="legacy")
    coordinator.data.climate_devices.update(unsupported=unsupported, legacy=legacy)
    config_entry = SimpleNamespace(
        runtime_data=SimpleNamespace(coordinator=coordinator),
        async_on_unload=lambda callback: None,
    )
    entities = []
    listeners = []
    coordinator.async_add_listener = lambda callback: (
        listeners.append(callback) or (lambda: None)
    )
    await async_setup_entry(None, config_entry, entities.extend)
    assert [entity._device_id for entity in entities] == [supported.unique_id]
    unsupported.supports_comfort_warm_floor = True
    listeners[0]()
    assert {entity._device_id for entity in entities} == {
        supported.unique_id,
        "unsupported",
    }
