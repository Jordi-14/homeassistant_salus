"""Entity diagnostics and activity must explain decisions without causing writes."""

import json
from pathlib import Path

import pytest

from tests.test_comfort_rule import NOW, OPTIONS, restart
from tests.test_comfort_rule import env as env
from tests.test_comfort_rule import rule_hass as rule_hass
from tests.test_minimum_comfort import minimum as minimum
from tests.test_minimum_comfort import outside, run, started


def activity(hass):
    entries = []
    hass.bus.async_listen("logbook_entry", lambda event: entries.append(dict(event.data)))
    return entries


async def test_observed_transitions_survive_restart_and_ignore_unavailable(env):
    controller = env["controller"]
    logs = activity(env["hass"])
    await controller.async_observe("select.room", "off")
    assert controller.entity_status("select.room")["comfort_last_off_at"] is None
    env["clock"].tick(60)
    await controller.async_observe("select.room", "level_1")
    stamp = controller.entity_status("select.room")["comfort_observed_on_at"]
    assert stamp is not None
    assert controller.entity_status("select.room")["comfort_on_time_basis"] == "observed_transition"
    await controller.async_observe("select.room", "unavailable")
    env["clock"].tick(60)
    await controller.async_observe("select.room", "level_3")
    assert controller.entity_status("select.room")["comfort_observed_on_at"] == stamp
    await restart(env)
    await env["controller"].async_observe("select.room", "level_3")
    assert env["controller"].entity_status("select.room")["comfort_observed_on_at"] == stamp
    await env["controller"].async_observe("select.room", "off")
    status = env["controller"].entity_status("select.room")
    assert status["comfort_observed_on_at"] is None
    assert status["comfort_last_off_at"] is not None
    await env["hass"].async_block_till_done()
    assert len(logs) == 3
    assert all(item["entity_id"] == "select.room" for item in logs)
    assert env["calls"] == []


async def test_first_seen_active_is_not_claimed_as_a_known_transition(env):
    await env["controller"].async_observe("select.room", "level_2")
    status = env["controller"].entity_status("select.room")
    assert status["comfort_on_time_basis"] == "already_active"
    assert status["comfort_observed_on_at"] is not None
    assert status["comfort_period_started_at"] is None
    assert status["comfort_next_check_at"] is None


async def test_entity_status_matches_independent_periods_pause_and_off(minimum):
    controller = minimum["controller"]
    await started(minimum, floor_entities=["select.room"])
    status = controller.entity_status("select.room")
    assert status["comfort_period_started_at"] == controller._time(NOW.timestamp())
    assert status["comfort_next_check_at"] == controller._time(NOW.timestamp() + 4 * 3600)
    evidence = status["comfort_start_evidence"]
    assert evidence["temperature_c"] == 2
    assert evidence["minimum_at"] is not None and evidence["fetched_at"] is not None
    minimum["clock"].tick(60)
    await run(minimum)
    assert controller.entity_status("select.room")["comfort_next_check_at"] == status["comfort_next_check_at"]
    assert controller.entity_status("select.second")["comfort_next_check_at"] is None
    minimum["hass"].states.async_set("automation.rule", "off")
    paused = controller.entity_status("select.room")
    assert paused["comfort_next_check_at"] is None
    assert paused["comfort_scheduled_check_at"] == status["comfort_next_check_at"]
    minimum["hass"].states.async_set("automation.rule", "on")
    assert controller.entity_status("select.room", "off")["comfort_next_check_at"] is None


async def test_delayed_confirmation_does_not_advertise_started_period(minimum):
    minimum["delay_state"] = True
    await run(minimum)
    status = minimum["controller"].entity_status("select.room")
    assert status["comfort_phase"] == "starting"
    assert status["comfort_period_started_at"] is None
    assert status["comfort_next_check_at"] is None


async def test_activity_has_start_evidence_extension_and_numeric_stop_reason(minimum):
    logs = activity(minimum["hass"])
    await started(minimum)
    for _ in range(4):
        minimum["clock"].tick(60)
        await run(minimum)
    outside(minimum, 4)
    minimum["clock"].tick(4 * 3600)
    await run(minimum)
    outside(minimum, 14)
    minimum["clock"].tick(3600)
    await run(minimum)
    await run(minimum)
    await minimum["hass"].async_block_till_done()
    messages = [item["message"] for item in logs]
    assert sum("Laveste prognose" in text for text in messages) == 1
    assert any("tændgrænse: under 5" in text and "Prognose hentet" in text for text in messages)
    assert sum("ny periode" in text for text in messages) == 1
    assert any("Ude nu: 14 °C, slukgrænse: 7 °C" in text for text in messages)
    assert all(item["entity_id"] == "select.room" for item in logs)
    assert minimum["calls"] == [("select.room", "level_1"), ("select.room", "off")]


async def test_observation_listener_tracks_only_salus_floor_selects(env):
    controller = env["controller"]
    controller.watch_room_limits()
    env["hass"].states.async_set("select.other", "level_1", {"options": OPTIONS})
    env["hass"].states.async_set("select.room", "level_1", {"options": OPTIONS})
    await env["hass"].async_block_till_done()
    assert controller.data["observations"]["select.room"]["level"] == "level_1"
    assert "select.other" not in controller.data["observations"]
    controller.close()
    env["hass"].states.async_set("select.room", "off", {"options": OPTIONS})
    await env["hass"].async_block_till_done()
    assert controller.data["observations"]["select.room"]["level"] == "level_1"


async def test_observation_save_failure_preserves_previous_timestamp(env, monkeypatch):
    await env["controller"].async_observe("select.room", "off")

    def fail(*_args):
        raise OSError("disk full")

    monkeypatch.setattr("custom_components.salus.comfort_rule._save", fail)
    await env["controller"].async_observe("select.room", "level_1")
    assert env["controller"].entity_status("select.room")["comfort_observed_on_at"] is None
    saved = json.loads(Path(env["controller"].path).read_text(encoding="utf-8"))
    assert saved["observations"]["select.room"]["level"] == "off"


@pytest.mark.parametrize("cold_at", [8, 9])
async def test_user_eight_hour_horizon_excludes_later_cold_and_uses_strict_threshold(minimum, cold_at):
    # Measured outside is warm. Every relevant forecast point is >=8 C.
    # Exactly 8 C must not start; a colder point beyond the horizon must not start.
    for index, row in enumerate(minimum["rows"]):
        row["temperature"] = 8 if index + 1 == cold_at else 12
        if index + 1 > 8:
            row["temperature"] = 2
    outside(minimum, 12.5)
    await run(minimum, forecast_hours=8, start_below=8, stop_at=10, min_runtime_hours=6)
    assert minimum["calls"] == []
