"""Floor-comfort discovery, confirmed state and command failures."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from salus_it600.exceptions import IT600ConnectionError, IT600ValidationError

from custom_components.salus.const import DOMAIN
from custom_components.salus.select import (
    SalusComfortWarmFloorSelect,
    async_setup_entry,
)
from tests.conftest import FakeCoordinator, make_climate_device


def setup_select(level=0, supported=True):
    device = make_climate_device(model="SQ610RFNH")
    device.advanced_settings = SimpleNamespace(comfort_warm_floor=level)
    device.supports_comfort_warm_floor = supported
    coordinator = FakeCoordinator()
    coordinator.data.climate_devices[device.unique_id] = device
    coordinator.gateway.set_climate_device_comfort_warm_floor = AsyncMock()
    return SalusComfortWarmFloorSelect(coordinator, device.unique_id), coordinator, device


@pytest.mark.parametrize("level,expected", [(0, "off"), (1, "level_1"), (2, "level_2"), (3, "level_3"), (4, None), (None, None), (True, None)])
def test_confirmed_options(level, expected):
    entity, _, _ = setup_select(level)
    assert entity.current_option == expected


def test_metadata_and_device_grouping():
    entity, _, device = setup_select()
    assert entity.unique_id == f"{device.unique_id}_comfort_warm_floor"
    assert entity.device_info["identifiers"] == {(DOMAIN, device.unique_id)}
    assert entity.entity_category == EntityCategory.CONFIG
    assert entity.entity_registry_enabled_default is False
    assert entity.translation_key == "comfort_warm_floor"
    assert entity.options == ["off", "level_1", "level_2", "level_3"]


async def test_command_keeps_reported_value_until_poll_confirms():
    entity, coordinator, device = setup_select()
    await entity.async_select_option("level_3")
    coordinator.gateway.set_climate_device_comfort_warm_floor.assert_awaited_once_with(device.unique_id, 3)
    assert coordinator.refresh_requests == 1
    assert entity.current_option == "off"
    device.advanced_settings.comfort_warm_floor = 3
    assert entity.current_option == "level_3"


async def test_invalid_option_never_calls_gateway():
    entity, coordinator, _ = setup_select()
    with pytest.raises(ServiceValidationError):
        await entity.async_select_option("level_4")
    coordinator.gateway.set_climate_device_comfort_warm_floor.assert_not_called()


async def test_transport_error_preserves_reported_state():
    entity, coordinator, _ = setup_select()
    coordinator.gateway.set_climate_device_comfort_warm_floor.side_effect = IT600ConnectionError("uncertain outcome")
    with pytest.raises(HomeAssistantError):
        await entity.async_select_option("level_3")
    assert entity.current_option == "off"
    assert coordinator.refresh_requests == 1


async def test_client_validation_error_is_not_reported_as_success():
    entity, coordinator, _ = setup_select()
    coordinator.gateway.set_climate_device_comfort_warm_floor.side_effect = IT600ValidationError("unsupported counter")
    with pytest.raises(ServiceValidationError, match="unsupported counter"):
        await entity.async_select_option("level_3")
    assert entity.current_option == "off"
    assert coordinator.refresh_requests == 0


async def test_unavailable_profile_never_calls_gateway():
    entity, coordinator, device = setup_select(supported=False)
    assert not entity.available
    with pytest.raises(ServiceValidationError):
        await entity.async_select_option("level_1")
    coordinator.gateway.set_climate_device_comfort_warm_floor.assert_not_called()
    device.supports_comfort_warm_floor = True
    device.available = False
    assert not entity.available
    device.available = True
    coordinator.data.climate_devices.clear()
    assert not entity.available
    assert entity.current_option is None


async def test_discovery_adds_only_supported_and_handles_late_devices():
    _, coordinator, device = setup_select()
    unsupported = make_climate_device(unique_id="other")
    coordinator.data.climate_devices[unsupported.unique_id] = unsupported
    coordinator.async_add_listener = Mock(return_value=lambda: None)
    entry = SimpleNamespace(runtime_data=SimpleNamespace(coordinator=coordinator), async_on_unload=Mock())
    add_entities = Mock()
    await async_setup_entry(None, entry, add_entities)
    assert [e.unique_id for e in add_entities.call_args.args[0]] == [f"{device.unique_id}_comfort_warm_floor"]
    unsupported.supports_comfort_warm_floor = True
    for call in coordinator.async_add_listener.call_args_list:
        call.args[0]()
    assert add_entities.call_count == 2
    for call in coordinator.async_add_listener.call_args_list:
        call.args[0]()
    assert add_entities.call_count == 2
