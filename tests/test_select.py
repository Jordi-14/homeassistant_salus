"""Floor-comfort discovery, confirmed state and command failures."""

from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock, Mock

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
    assert entity.entity_registry_enabled_default is True
    assert entity.translation_key == "comfort_warm_floor"
    assert entity.options == ["off", "level_1", "level_2", "level_3"]


async def test_command_keeps_reported_value_until_poll_confirms():
    entity, coordinator, device = setup_select()
    await entity.async_select_option("level_3")
    coordinator.gateway.set_climate_device_comfort_warm_floor.assert_awaited_once_with(
        device.unique_id, 3, before_write=ANY, confirmation_timeout=120,
    )
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


async def test_select_persists_backup_before_gateway_dispatch(tmp_path):
    import json

    entity, coordinator, _ = setup_select()
    path = tmp_path / "private" / "backup.json"
    entity.hass = SimpleNamespace(
        config=SimpleNamespace(path=lambda *args: str(path)),
        async_add_executor_job=AsyncMock(side_effect=lambda function, *args: function(*args)),
    )
    snapshot = {"private": "thermostat settings"}

    async def command(*args, before_write, **kwargs):
        await before_write(snapshot)
        assert json.loads(path.read_text())["before"] == snapshot

    coordinator.gateway.set_climate_device_comfort_warm_floor.side_effect = command
    await entity.async_select_option("level_1")
    data = json.loads(path.read_text())
    assert data["requested_level"] == 1
    assert data["saved_at"]


async def test_backup_disk_error_blocks_dispatch(monkeypatch):
    entity, coordinator, _ = setup_select()
    entity.hass = SimpleNamespace(
        config=SimpleNamespace(path=lambda *args: "backup.json"),
        async_add_executor_job=AsyncMock(side_effect=OSError("disk full")),
    )
    dispatched = False

    async def command(*args, before_write, **kwargs):
        nonlocal dispatched
        await before_write({"snapshot": True})
        dispatched = True

    coordinator.gateway.set_climate_device_comfort_warm_floor.side_effect = command
    with pytest.raises(HomeAssistantError, match="backup failed"):
        await entity.async_select_option("level_1")
    assert not dispatched
    assert coordinator.refresh_requests == 1


def test_atomic_writer_failure_is_not_swallowed(tmp_path, monkeypatch):
    from homeassistant.util.file import WriteError

    from custom_components.salus.floor_backup import persist_floor_backup

    writer = Mock(side_effect=WriteError("disk full"))
    monkeypatch.setattr("custom_components.salus.floor_backup.write_utf8_file_atomic", writer)
    with pytest.raises(WriteError):
        persist_floor_backup(str(tmp_path / "backup.json"), {"before": "snapshot"})


def test_old_backup_cannot_masquerade_as_new_backup(tmp_path, monkeypatch):
    from custom_components.salus.floor_backup import persist_floor_backup
    path = tmp_path / "backup.json"
    path.write_text('{"before": "old"}')
    monkeypatch.setattr("custom_components.salus.floor_backup.write_utf8_file_atomic", Mock())
    with pytest.raises(OSError, match="did not match"):
        persist_floor_backup(str(path), {"before": "new"})

async def test_app_update_keeps_entity_available_until_off_is_reported():
    import copy

    from salus_it600.comfort_warm_floor import build_comfort_warm_floor_command
    from salus_it600.parsers.climate import parse_climate_device

    # Anonymized captured layout, with a synthetic identity and level 1.
    blob = bytearray.fromhex('720701000001050040000000000104002700100006003500050040000500010000000101800000000dfe010000000100ffffffffffffffffffffffffffffffffffffffffffffffffffffff0000')
    blob[39] = 1
    before = {
        'status': 'success',
        'data': {'UniID': 'test-floor', 'Endpoint': 9, 'DeviceType': 100},
        'DeviceL': {'ModelIdentifier_i': 'SQ610RFNH'},
        'sZDO': {'FirmwareVersion': '00000054'},
        'sZDOInfo': {'OnlineStatus_i': 1},
        'sIT600TH': {'Schedule': blob.hex(), 'Status_2_d': blob.hex(),
                     'PairedTRVShortID': 'F' * 24, 'PairedWCNumber': 1,
                     'SystemMode': 4, 'HoldType': 2, 'HeatingSetpoint_x100': 2100},
        'sIT600I': {'CommandResponse_d': '42313173' + blob[1:60].hex() + '00'},
    }
    command = build_comfort_warm_floor_command(before, 0)
    pending = copy.deepcopy(before)
    pending['sIT600I']['CommandResponse_d'] = command + '00'
    after = copy.deepcopy(pending)
    after['sIT600TH']['Schedule'] = after['sIT600TH']['Status_2_d'] = '72' + command[8:] + blob[60:].hex()
    coordinator = FakeCoordinator()
    entity = SalusComfortWarmFloorSelect(coordinator, 'test-floor')
    for status, option in [(before, 'level_1'), (pending, 'level_1'), (after, 'off')]:
        coordinator.data.climate_devices['test-floor'] = parse_climate_device(status)
        assert entity.available
        assert entity.current_option == option
    offline = copy.deepcopy(after)
    offline['sZDOInfo']['OnlineStatus_i'] = 0
    coordinator.data.climate_devices['test-floor'] = parse_climate_device(offline)
    assert not entity.available
