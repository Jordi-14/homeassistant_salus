"""Run the actual blueprint actions in HA with simulated weather and selects."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from freezegun import freeze_time
from homeassistant.components.automation.config import (
    AUTOMATION_BLUEPRINT_SCHEMA,
    PLATFORM_SCHEMA,
)
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.script import Script
from homeassistant.util import yaml as yaml_util

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "blueprints/automation/salus_floor_weather.yaml"
NOW = datetime(2026, 10, 25, 12, tzinfo=UTC)
OPTIONS = ["off", "level_1", "level_2", "level_3"]


def configuration(**inputs):
    """Use HA's actual blueprint parser and input substitution."""
    blueprint = Blueprint(
        yaml_util.load_yaml_dict(str(PATH)),
        expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA,
    )
    instance = BlueprintInputs(blueprint, {"use_blueprint": {"path": str(PATH), "input": {
        "floor_entities": ["select.room"], "weather_source": "weather.test", **inputs,
    }}})
    instance.validate()
    return instance.async_substitute()


def forecast(temperature=2, *, count=24, unit="°C"):
    """One entry for every hour ahead, including the end of the horizon."""
    return [{"datetime": (NOW + timedelta(hours=i + 1)).isoformat(),
             "temperature": temperature if unit == "°C" else temperature * 9 / 5 + 32}
            for i in range(count)]


@pytest.mark.parametrize("inputs", [{}, {"always_enabled": False, "weather_source": "", "outdoor_sensor": "sensor.outside"}])
async def test_complete_automation_schema_including_triggers(inputs):
    assert PLATFORM_SCHEMA(configuration(**inputs))


@pytest.fixture
async def rule_env(tmp_path):
    """No integration setup, gateway connections or actual device writes."""
    with freeze_time(NOW, real_asyncio=True) as clock:
        hass = HomeAssistant(str(tmp_path))
        await hass.config.async_set_time_zone("Europe/Copenhagen")
        env = {"hass": hass, "clock": clock, "calls": [], "forecast_calls": 0, "rows": forecast()}
        hass.states.async_set("weather.test", "cloudy", {"temperature": 8, "temperature_unit": "°C"})
        hass.states.async_set("select.room", "off", {"options": OPTIONS})

        async def get_forecast(call):
            assert call.data["type"] == "hourly"
            assert call.data["entity_id"] in ("weather.test", ["weather.test"])
            env["forecast_calls"] += 1
            if env.get("forecast_error"):
                raise HomeAssistantError("test provider offline")
            return {"weather.test": {"forecast": deepcopy(env["rows"])}}

        async def set_level(call):
            env["calls"].append(dict(call.data))
            entity = call.data["entity_id"]
            if isinstance(entity, list):
                entity = entity[0]
            hass.states.async_set(entity, call.data["option"], {"options": OPTIONS})

        hass.services.async_register("weather", "get_forecasts", get_forecast, supports_response=SupportsResponse.ONLY)
        hass.services.async_register("select", "select_option", set_level)
        yield env
        await hass.async_stop()


async def run_rule(env, **inputs):
    config = configuration(**inputs)
    actions = config.get("actions", config.get("action"))
    script = Script(env["hass"], cv.SCRIPT_SCHEMA(actions), "SALUS weather test", "salus", script_mode="single")
    await script.async_run(config["variables"])
    await env["hass"].async_block_till_done()


@pytest.mark.parametrize(("peak", "expected"), [(2, "level_3"), (5, "level_2"), (15, "level_2")])
async def test_all_24_hours_must_be_cold_and_day_rule_has_priority(rule_env, peak, expected):
    rule_env["rows"][12]["temperature"] = peak
    await run_rule(rule_env, schedule_level="level_2", always_level="level_3")
    assert rule_env["calls"][0]["option"] == expected


async def test_one_cold_hour_does_not_enable_all_day(rule_env):
    rule_env["rows"] = forecast(15)
    rule_env["rows"][0]["temperature"] = -5
    await run_rule(rule_env, schedule_enabled=False)
    assert rule_env["calls"] == []


@pytest.mark.parametrize("mutate", ["short", "gap", "missing_value", "nan", "bad_time", "empty"])
async def test_incomplete_or_invalid_forecast_preserves_current_level(rule_env, mutate):
    rule_env["hass"].states.async_set("select.room", "level_2", {"options": OPTIONS})
    if mutate == "short":
        rule_env["rows"] = forecast(2, count=12)
    elif mutate == "gap":
        rule_env["rows"][12] = deepcopy(rule_env["rows"][11])
    elif mutate == "missing_value":
        del rule_env["rows"][5]["temperature"]
    elif mutate == "nan":
        rule_env["rows"][5]["temperature"] = "nan"
    elif mutate == "bad_time":
        rule_env["rows"][5]["datetime"] = "invalid"
    else:
        rule_env["rows"] = []
    await run_rule(rule_env)
    assert rule_env["calls"] == []


async def test_forecast_failure_does_not_turn_comfort_off(rule_env):
    rule_env["forecast_error"] = True
    rule_env["hass"].states.async_set("select.room", "level_2", {"options": OPTIONS})
    with pytest.raises(HomeAssistantError):
        await run_rule(rule_env)
    assert rule_env["calls"] == []


@pytest.mark.parametrize(("start", "end", "expected"), [
    ("06:00:00", "22:00:00", "level_1"),
    ("22:00:00", "06:00:00", "off"),
    ("12:00:00", "14:00:00", "level_1"),
    ("06:00:00", "13:00:00", "off"),
    ("06:00:00", "06:00:00", "level_1"),
])
async def test_local_window_and_exact_end_boundary(rule_env, start, end, expected):
    # Frozen UTC noon is 13:00 local, after the autumn DST transition.
    initial = "off" if expected != "off" else "level_1"
    rule_env["hass"].states.async_set("select.room", initial, {"options": OPTIONS})
    await run_rule(rule_env, always_enabled=False, start_time=start, end_time=end)
    assert rule_env["calls"][0]["option"] == expected
    assert rule_env["forecast_calls"] == 0


async def test_own_outdoor_sensor_overrides_weather_current_temperature(rule_env):
    rule_env["hass"].states.async_set("sensor.outside", "20", {"unit_of_measurement": "°C"})
    await run_rule(rule_env, outdoor_sensor="sensor.outside", always_enabled=False)
    assert rule_env["calls"] == []


async def test_unavailable_sensor_does_not_use_weather_as_fallback(rule_env):
    rule_env["hass"].states.async_set("sensor.outside", "unavailable", {"unit_of_measurement": "°C"})
    await run_rule(rule_env, outdoor_sensor="sensor.outside", always_enabled=False)
    assert rule_env["calls"] == []


async def test_fahrenheit_forecast_and_current_are_converted(rule_env):
    rule_env["rows"] = forecast(2, unit="°F")
    rule_env["hass"].states.async_set("weather.test", "cloudy", {"temperature": 46.4, "temperature_unit": "°F"})
    await run_rule(rule_env, always_level="level_3")
    assert rule_env["calls"][0]["option"] == "level_3"


async def test_no_repeated_write_for_unchanged_result(rule_env):
    await run_rule(rule_env)
    await run_rule(rule_env)
    assert len(rule_env["calls"]) == 1


@pytest.mark.parametrize(("current", "temperature", "expected"), [
    ("off", 12.5, None), ("off", 11.9, "level_1"),
    ("level_1", 12.5, None), ("level_1", 13, "off"),
])
async def test_hysteresis_prevents_boundary_flapping(rule_env, current, temperature, expected):
    rule_env["hass"].states.async_set("select.room", current, {"options": OPTIONS})
    rule_env["hass"].states.async_set("weather.test", "cloudy", {"temperature": temperature, "temperature_unit": "°C"})
    await run_rule(rule_env, always_enabled=False)
    assert [call["option"] for call in rule_env["calls"]] == ([] if expected is None else [expected])


async def test_both_rules_disabled_is_inert(rule_env):
    await run_rule(rule_env, schedule_enabled=False, always_enabled=False)
    assert rule_env["calls"] == []
    assert rule_env["forecast_calls"] == 0


async def test_unavailable_and_non_floor_targets_are_skipped(rule_env):
    rule_env["hass"].states.async_set("select.room", "unavailable", {"options": OPTIONS})
    rule_env["hass"].states.async_set("select.other", "off", {"options": ["off", "on"]})
    await run_rule(rule_env, floor_entities=["select.room", "select.other"])
    assert rule_env["calls"] == []


@pytest.mark.parametrize(("hour", "expected"), [(21, "level_1"), (0, "level_1"), (5, None)])
async def test_overnight_window_in_local_timezone(rule_env, hour, expected):
    rule_env["clock"].move_to(NOW.replace(hour=hour))
    await run_rule(rule_env, always_enabled=False, start_time="22:00:00", end_time="06:00:00")
    assert [call["option"] for call in rule_env["calls"]] == ([] if expected is None else [expected])


async def test_sensor_only_mode_needs_no_weather_provider(rule_env):
    rule_env["hass"].states.async_set("sensor.outside", "3", {"unit_of_measurement": "°C"})
    await run_rule(rule_env, always_enabled=False, weather_source="", outdoor_sensor="sensor.outside")
    assert rule_env["calls"][0]["option"] == "level_1"
    assert rule_env["forecast_calls"] == 0


@pytest.mark.parametrize("state", ["unavailable", "unknown"])
async def test_offline_weather_does_not_use_stale_current_attributes(rule_env, state):
    rule_env["hass"].states.async_set("weather.test", state, {"temperature": 2, "temperature_unit": "°C"})
    await run_rule(rule_env, always_enabled=False)
    assert rule_env["calls"] == []


async def test_unknown_temperature_unit_does_not_trigger_heating(rule_env):
    rule_env["hass"].states.async_set("weather.test", "cloudy", {"temperature": 2, "temperature_unit": "unknown"})
    await run_rule(rule_env)
    assert rule_env["calls"] == []


async def test_past_cold_hours_are_not_used_for_next_day(rule_env):
    rule_env["rows"] = [
        {"datetime": (NOW - timedelta(hours=i)).isoformat(), "temperature": -10}
        for i in range(1, 25)
    ] + forecast(15)
    await run_rule(rule_env, schedule_enabled=False)
    assert rule_env["calls"] == []


async def test_two_rooms_only_write_to_the_one_that_needs_change(rule_env):
    rule_env["hass"].states.async_set("select.second", "level_2", {"options": OPTIONS})
    await run_rule(rule_env, floor_entities=["select.room", "select.second"], always_level="level_2")
    assert len(rule_env["calls"]) == 1
    assert rule_env["calls"][0]["option"] == "level_2"


async def test_write_failure_stops_sequence_without_replay(rule_env):
    calls = []

    async def fail_write(call):
        calls.append(dict(call.data))
        raise HomeAssistantError("test unconfirmed command")

    rule_env["hass"].services.async_register("select", "select_option", fail_write)
    rule_env["hass"].states.async_set("select.second", "off", {"options": OPTIONS})
    with pytest.raises(HomeAssistantError):
        await run_rule(rule_env, floor_entities=["select.room", "select.second"])
    assert len(calls) == 1
