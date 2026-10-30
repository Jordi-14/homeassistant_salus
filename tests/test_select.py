"""Opt-in comfort control returns on acknowledgement and confirms through polls."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import HomeAssistantError
from salus_it600.exceptions import IT600ConnectionError

from custom_components.salus.select import SalusComfortWarmFloorSelect
from tests.conftest import FakeCoordinator, make_climate_device


def setup_select():
    device = make_climate_device(model='SQ610RFNH')
    device.advanced_settings = SimpleNamespace(comfort_warm_floor=0)
    device.supports_comfort_warm_floor = True
    coordinator = FakeCoordinator()
    coordinator.data.climate_devices[device.unique_id] = device
    coordinator.gateway.set_climate_device_comfort_warm_floor = AsyncMock()
    return SalusComfortWarmFloorSelect(coordinator, device.unique_id), coordinator, device


def test_floor_select_is_opt_in_and_has_no_controller_attributes():
    entity, _, _ = setup_select()
    assert entity.entity_registry_enabled_default is False
    assert entity.translation_key == 'comfort_warm_floor'
    assert entity.extra_state_attributes is None


async def test_ack_returns_requested_level_as_assumed_until_poll_confirms():
    entity, coordinator, device = setup_select()
    await entity.async_select_option('level_3')
    coordinator.gateway.set_climate_device_comfort_warm_floor.assert_awaited_once_with(device.unique_id, 3)
    assert entity.current_option == 'level_3'
    assert entity.assumed_state
    assert not coordinator.gateway_lock.locked()
    async with asyncio.timeout(.1):
        async with coordinator.gateway_lock:
            pass  # Other polls and commands can proceed during confirmation.
    device.advanced_settings.comfort_warm_floor = 3
    assert entity.current_option == 'level_3'
    assert not entity.assumed_state
    assert coordinator.refresh_requests == 1


async def test_pending_window_is_longer_than_thirty_seconds_but_bounded():
    entity, _, _ = setup_select()
    now = [0]
    entity._loop_time = lambda: now[0]
    await entity.async_select_option('level_1')
    now[0] = 60
    assert entity.current_option == 'level_1' and entity.assumed_state
    now[0] = 121
    assert entity.current_option == 'off' and not entity.assumed_state


async def test_failed_write_clears_optimistic_state_and_does_not_replay():
    entity, coordinator, _ = setup_select()
    coordinator.gateway.set_climate_device_comfort_warm_floor.side_effect = IT600ConnectionError('lost')
    with pytest.raises(HomeAssistantError):
        await entity.async_select_option('level_1')
    assert entity.current_option == 'off'
    assert not entity.assumed_state
    assert coordinator.gateway.set_climate_device_comfort_warm_floor.await_count == 1
