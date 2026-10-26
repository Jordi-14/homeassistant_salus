"""Minimum periods, independent rooms and explicit manual takeover."""

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er

from custom_components.salus.comfort_rule import ComfortRules
from tests.test_comfort_rule import (
    CONFIG,
    NOW,
    OPTIONS,
    hourly_forecast,
    restart,
)
from tests.test_comfort_rule import (
    env as env,
)
from tests.test_comfort_rule import (
    rule_hass as rule_hass,
)

ROOM_LOOKUP = ComfortRules._room_temperature


@pytest.fixture
def minimum(env, monkeypatch):
    env['rooms'] = {'select.room': 22.0, 'select.second': 22.0}
    monkeypatch.setattr(ComfortRules, '_room_temperature', lambda self, entity: (env['rooms'].get(entity), 'climate.' + entity.split('.')[1]))
    hourly_forecast(env, 2)
    env['hass'].states.async_set('weather.test', 'cloudy', {'temperature': 14, 'temperature_unit': '°C'})
    return env


async def run(env, **kwargs):
    return await env['controller'].async_evaluate({**CONFIG, 'cycle_mode': 'minimum', 'source': 'weather.test',
                                                  'source_mode': 'forecast', **kwargs})


async def started(env, **kwargs):
    await run(env, **kwargs)
    await run(env, **kwargs)
    return env['controller'].data['devices']['select.room']


def outside(env, value):
    env['hass'].states.async_set('weather.test', 'cloudy', {'temperature': value, 'temperature_unit': '°C'})


async def test_future_cold_starts_even_while_current_is_warm_and_protects_minimum(minimum):
    record = await started(minimum)
    assert record['minimum_until'] == NOW.timestamp() + 4 * 3600
    original = record['next_check_at']
    for _ in range(5):
        minimum['clock'].tick(60)
        result = await run(minimum)
        assert result['rooms']['select.room']['decision'] == 'minimum_runtime'
        assert record['next_check_at'] == original
    assert len(minimum['calls']) == 1
    assert minimum['forecast_calls'] == 1


async def test_actual_confirmation_starts_full_minimum_not_first_dispatch(minimum):
    minimum['delay_state'] = True
    await run(minimum)
    record = minimum['controller'].data['devices']['select.room']
    assert record['minimum_until'] is None
    minimum['clock'].tick(20)
    minimum['hass'].states.async_set('select.room', 'level_1', {'options': OPTIONS})
    await run(minimum)
    assert record['active_at'] == NOW.timestamp() + 20
    assert record['minimum_until'] == NOW.timestamp() + 20 + 4 * 3600


async def test_warm_now_stops_only_at_minimum_end(minimum):
    await started(minimum)
    minimum['clock'].tick(4 * 3600 - 1)
    await run(minimum)
    assert len(minimum['calls']) == 1
    minimum['clock'].tick(1)
    result = await run(minimum)
    assert minimum['calls'][-1] == ('select.room', 'off')
    assert result['rooms']['select.room']['decision'] == 'stopped'


async def test_cold_extends_one_hour_and_ignores_changes_inside_period(minimum):
    await started(minimum)
    outside(minimum, 4)
    minimum['clock'].tick(4 * 3600)
    result = await run(minimum)
    record = minimum['controller'].data['devices']['select.room']
    assert result['rooms']['select.room']['decision'] == 'extended'
    assert record['next_check_at'] == NOW.timestamp() + 5 * 3600
    outside(minimum, 14)
    minimum['clock'].tick(59 * 60)
    await run(minimum)
    assert len(minimum['calls']) == 1
    minimum['clock'].tick(60)
    await run(minimum)
    assert minimum['calls'][-1][1] == 'off'


async def test_later_forecast_never_changes_an_active_cycle_or_gets_fetched(minimum):
    record = await started(minimum)
    outside(minimum, 4)
    minimum['forecast_error'] = True
    minimum['rows'] = []
    minimum['clock'].tick(4 * 3600)
    await run(minimum)
    assert record['phase'] == 'running'
    assert record['next_check_at'] == NOW.timestamp() + 5 * 3600
    assert minimum['forecast_calls'] == 1


async def test_outdoor_sensor_has_priority_then_current_weather_fallback(minimum):
    minimum['hass'].states.async_set('sensor.probe', '3', {'unit_of_measurement': '°C'})
    await started(minimum, outdoor_sensor='sensor.probe')
    minimum['clock'].tick(4 * 3600)
    result = await run(minimum, outdoor_sensor='sensor.probe')
    assert result['stop_temperature_c'] == 3
    assert result['current_temperature_data']['source'] == 'sensor.probe'
    minimum['hass'].states.async_set('sensor.probe', 'unavailable')
    minimum['clock'].tick(3600)
    result = await run(minimum, outdoor_sensor='sensor.probe')
    assert result['stop_temperature_c'] == 14
    assert result['current_temperature_data']['fallback_used']
    assert minimum['calls'][-1][1] == 'off'


async def test_missing_all_current_readings_extends_without_guessing(minimum):
    await started(minimum)
    minimum['hass'].states.async_set('weather.test', 'unavailable')
    minimum['clock'].tick(4 * 3600)
    result = await run(minimum)
    assert result['rooms']['select.room']['last_extension_reason'] == 'outdoor_missing'
    assert len(minimum['calls']) == 1


async def test_room_minimum_holds_only_its_own_room(minimum):
    hass = minimum['hass']
    er.async_get(hass).async_get_or_create('select', 'salus', 'second_comfort_warm_floor', suggested_object_id='second')
    hass.states.async_set('select.second', 'off', {'options': OPTIONS})
    config = {'floor_entities': ['select.room', 'select.second'], 'use_room_minimum': True}
    minimum['rooms']['select.room'] = 20
    await started(minimum, **config)
    minimum['clock'].tick(4 * 3600)
    result = await run(minimum, **config)
    assert hass.states.get('select.room').state == 'level_1'
    assert hass.states.get('select.second').state == 'off'
    assert result['rooms']['select.room']['room_hold']
    assert result['rooms']['select.room']['last_extension_reason'] == 'room_hold'
    assert not result['rooms']['select.second']['room_hold']


async def test_room_hysteresis_is_remembered_over_restart(minimum):
    minimum['rooms']['select.room'] = 20.8
    await started(minimum, use_room_minimum=True)
    minimum['rooms']['select.room'] = 21.2
    await restart(minimum)
    minimum['clock'].tick(4 * 3600)
    result = await run(minimum, use_room_minimum=True)
    assert result['rooms']['select.room']['room_hold']
    minimum['rooms']['select.room'] = 21.5
    minimum['clock'].tick(3600)
    await run(minimum, use_room_minimum=True)
    assert minimum['calls'][-1][1] == 'off'


async def test_missing_room_reading_does_not_stop_or_start_other_rooms(minimum):
    minimum['rooms']['select.room'] = None
    await started(minimum, use_room_minimum=True)
    minimum['clock'].tick(4 * 3600)
    result = await run(minimum, use_room_minimum=True)
    assert result['rooms']['select.room']['last_extension_reason'] == 'room_temperature_missing'
    assert len(minimum['calls']) == 1


async def test_cold_room_alone_cannot_start(minimum):
    hourly_forecast(minimum, 12)
    minimum['rooms']['select.room'] = 18
    await run(minimum, use_room_minimum=True)
    assert not minimum['calls']


async def test_manual_takeover_opt_in_preserves_level_and_never_resets_clock(minimum):
    minimum['hass'].states.async_set('select.room', 'level_3', {'options': OPTIONS})
    await run(minimum)
    assert 'select.room' not in minimum['controller'].data['devices']
    result = await run(minimum, adopt_manual=True)
    record = minimum['controller'].data['devices']['select.room']
    assert result['rooms']['select.room']['decision'] == 'adopted'
    assert record['level'] == 'level_3'
    assert record['active_at'] == NOW.timestamp()
    first_check = record['next_check_at']
    minimum['clock'].tick(60)
    await restart(minimum)
    await run(minimum, adopt_manual=True)
    assert minimum['controller'].data['devices']['select.room']['next_check_at'] == first_check
    assert not minimum['calls']


async def test_takeover_waits_until_the_start_condition_becomes_true(minimum):
    minimum['hass'].states.async_set('select.room', 'level_2', {'options': OPTIONS})
    hourly_forecast(minimum, 12)
    await run(minimum, adopt_manual=True)
    assert not minimum['controller'].data['devices']
    minimum['clock'].tick(16 * 60)
    hourly_forecast(minimum, 2)
    await run(minimum, adopt_manual=True)
    assert minimum['controller'].data['devices']['select.room']['active_at'] == NOW.timestamp() + 16 * 60
    assert not minimum['calls']


async def test_staggered_takeover_gets_its_own_minimum_period(minimum):
    await started(minimum, adopt_manual=True)
    minimum['clock'].tick(3600)
    er.async_get(minimum['hass']).async_get_or_create('select', 'salus', 'second_comfort_warm_floor', suggested_object_id='second')
    minimum['hass'].states.async_set('select.second', 'level_3', {'options': OPTIONS})
    await run(minimum, adopt_manual=True, floor_entities=['select.room', 'select.second'])
    devices = minimum['controller'].data['devices']
    assert devices['select.room']['minimum_until'] == NOW.timestamp() + 4 * 3600
    assert devices['select.second']['minimum_until'] == NOW.timestamp() + 5 * 3600
    minimum['clock'].tick(3 * 3600)
    await minimum['controller'].async_deadlines()
    assert minimum['hass'].states.get('select.room').state == 'off'
    assert minimum['hass'].states.get('select.second').state == 'level_3'
    assert len(minimum['calls']) == 2  # first room on/off; second only adopted


async def test_manual_off_interrupts_minimum_and_starts_room_pause(minimum):
    await started(minimum)
    minimum['hass'].states.async_set('select.room', 'off', {'options': OPTIONS})
    await run(minimum, adopt_manual=True)
    record = minimum['controller'].data['devices']['select.room']
    assert record['phase'] == 'cooldown'
    assert record['restart_after'] == NOW.timestamp() + 6 * 3600
    minimum['hass'].states.async_set('select.room', 'level_2', {'options': OPTIONS})
    await run(minimum, adopt_manual=True)
    assert not record['adopted']
    assert len(minimum['calls']) == 1


async def test_period_timer_and_post_restart_overdue_check_need_no_forecast(minimum):
    record = await started(minimum)
    expected = record['next_check_at']
    minimum['clock'].tick(5 * 3600)
    controller = await restart(minimum)
    assert controller.data['devices']['select.room']['next_check_at'] == expected
    await controller.async_deadlines()
    assert minimum['calls'][-1][1] == 'off'


async def test_downtime_does_not_replay_all_missed_hourly_checks(minimum):
    await started(minimum)
    outside(minimum, 4)
    minimum['clock'].tick(12 * 3600)
    await restart(minimum)
    await minimum['controller'].async_deadlines()
    record = minimum['controller'].data['devices']['select.room']
    assert record['next_check_at'] == NOW.timestamp() + 13 * 3600
    assert len(minimum['calls']) == 1


async def test_disabling_rule_pauses_stop_decisions_without_resetting_time(minimum):
    record = await started(minimum)
    check = record['next_check_at']
    minimum['hass'].states.async_set('automation.rule', 'off')
    minimum['clock'].tick(5 * 3600)
    await minimum['controller'].async_deadlines()
    assert len(minimum['calls']) == 1
    assert record['next_check_at'] == check
    minimum['hass'].states.async_set('automation.rule', 'on')
    await run(minimum)
    assert minimum['calls'][-1][1] == 'off'


async def test_upgrade_existing_cycle_preserves_original_start_time(minimum):
    await minimum['controller'].async_evaluate(CONFIG)
    await minimum['controller'].async_evaluate(CONFIG)
    minimum['clock'].tick(3600)
    await run(minimum)
    record = minimum['controller'].data['devices']['select.room']
    assert record['active_at'] == NOW.timestamp()
    assert record['minimum_until'] == NOW.timestamp() + 4 * 3600
    assert record['deadline'] is None


async def test_new_cycle_never_uses_legacy_maximum_even_if_supplied(minimum):
    record = await started(minimum, min_runtime_hours=5, max_runtime_hours=.25)
    assert record['deadline'] is None
    minimum['clock'].tick(3600)
    await minimum['controller'].async_deadlines()
    assert len(minimum['calls']) == 1


async def test_storage_failure_blocks_takeover_without_writing(minimum, monkeypatch):
    minimum['hass'].states.async_set('select.room', 'level_2', {'options': OPTIONS})
    monkeypatch.setattr('custom_components.salus.comfort_rule._save', lambda *_: (_ for _ in ()).throw(OSError('full')))
    with pytest.raises(HomeAssistantError):
        await run(minimum, adopt_manual=True)
    assert not minimum['calls']


async def test_invalid_outdoor_sensor_never_dispatches(minimum):
    with pytest.raises(ServiceValidationError):
        await run(minimum, outdoor_sensor='light.not_a_temperature')
    assert not minimum['calls']


async def test_failed_takeover_save_does_not_take_ownership_in_memory(minimum, monkeypatch):
    from custom_components.salus import comfort_rule as module
    original_save = module._save

    def fail_takeover_only(path, data):
        if data['devices']:
            raise OSError('disk full at takeover')
        original_save(path, data)

    minimum['hass'].states.async_set('select.room', 'level_3', {'options': OPTIONS})
    monkeypatch.setattr(module, '_save', fail_takeover_only)
    with pytest.raises(HomeAssistantError):
        await run(minimum, adopt_manual=True)
    assert 'select.room' not in minimum['controller'].data['devices']
    assert not minimum['calls']


def test_room_lookup_uses_same_device_and_refuses_ambiguity(minimum, monkeypatch):
    floors = {'select.room': SimpleNamespace(device_id='one'), 'select.second': SimpleNamespace(device_id='two')}
    climates = [SimpleNamespace(entity_id='climate.room', domain='climate', platform='salus', disabled=False, device_id='one'),
                SimpleNamespace(entity_id='climate.second', domain='climate', platform='salus', disabled=False, device_id='two')]
    monkeypatch.setattr(er, 'async_get', lambda _: SimpleNamespace(async_get=lambda entity: floors[entity]))
    monkeypatch.setattr(er, 'async_entries_for_device', lambda registry, device: [e for e in climates if e.device_id == device])
    minimum['hass'].states.async_set('climate.room', 'heat', {'current_temperature': 68, 'temperature_unit': '°F'})
    minimum['hass'].states.async_set('climate.second', 'heat', {'current_temperature': 17, 'temperature_unit': '°C'})
    controller = minimum['controller']
    assert ROOM_LOOKUP(controller, 'select.room') == (20, 'climate.room')
    assert ROOM_LOOKUP(controller, 'select.second') == (17, 'climate.second')
    climates.append(SimpleNamespace(entity_id='climate.ambiguous', domain='climate', platform='salus', disabled=False, device_id='one'))
    assert ROOM_LOOKUP(controller, 'select.room') == (None, None)


async def test_minimum_report_is_json_serializable_and_contains_independent_times(minimum):
    await started(minimum)
    result = await run(minimum)
    json.dumps(result, allow_nan=False)
    room = result['rooms']['select.room']
    assert datetime.fromisoformat(room['minimum_until']).timestamp() == NOW.timestamp() + 4 * 3600
    assert room['maximum_stop_at'] is None
    assert room['next_check_at'] == room['minimum_until']
    saved = json.loads(Path(minimum['controller'].path).read_text())
    assert saved['devices']['select.room']['room_hold'] is False
