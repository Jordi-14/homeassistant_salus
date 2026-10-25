"""Exercise persistent cycles with HA services and simulated temperatures."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import voluptuous as vol
from freezegun import freeze_time
from homeassistant.components.automation.config import (
    AUTOMATION_BLUEPRINT_SCHEMA,
    PLATFORM_SCHEMA,
)
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.core import Context, HomeAssistant, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.script import Script
from homeassistant.helpers.trace import trace_get
from homeassistant.util import yaml as yaml_util

from custom_components.salus import comfort_rule as module
from custom_components.salus.comfort_rule import (
    ComfortRules,
    _config,
    _load,
    async_setup_comfort_rules,
)

OPTIONS = ["off", "level_1", "level_2", "level_3"]
NOW = datetime(2026, 10, 25, 18, tzinfo=UTC)
CONFIG = {"rule_id": "automation.rule", "floor_entities": ["select.room"], "source": "sensor.outside"}


@pytest.fixture
def rule_hass(request):
    """Use the complete HA registry setup in CI and an isolated local fallback."""
    try:
        return request.getfixturevalue("hass")
    except pytest.FixtureLookupError:
        return None


@pytest.fixture
async def env(rule_hass, tmp_path):
    with freeze_time(NOW, real_asyncio=True) as clock:
        hass = rule_hass or HomeAssistant(str(tmp_path))
        # The controller deliberately uses real atomic files rather than HA's
        # mocked Store. Each test must therefore have its own config directory.
        hass.config.config_dir = str(tmp_path)
        if not hasattr(er.async_get(hass), "entities"):
            await er.async_get(hass).async_load()
        entry = er.async_get(hass).async_get_or_create("select", "salus", "test_comfort_warm_floor", suggested_object_id="room")
        assert entry.entity_id == "select.room"
        hass.states.async_set("select.room", "off", {"options": OPTIONS})
        hass.states.async_set("sensor.outside", "4", {"unit_of_measurement": "°C"})
        hass.states.async_set("weather.test", "cloudy", {"temperature": 4, "temperature_unit": "°C"})
        hass.states.async_set("automation.rule", "on")
        controller = ComfortRules(hass)
        await controller.async_load()
        result = {"hass": hass, "controller": controller, "clock": clock, "calls": [], "forecast_calls": 0}

        async def select(call):
            entity = call.data["entity_id"]
            result["calls"].append((entity, call.data["option"]))
            # Journal must be on disk before any dispatch.
            saved = json.loads(Path(controller.path).read_text(encoding="utf-8"))
            assert saved["devices"][entity]["phase"] in ("starting", "stopping")
            if result.get("command_error"):
                raise HomeAssistantError("test lost reply")
            if not result.get("delay_state"):
                hass.states.async_set(entity, call.data["option"], {"options": OPTIONS})

        async def forecast(call):
            result["forecast_calls"] += 1
            if result.get("forecast_error"):
                raise HomeAssistantError("test provider offline")
            return {"weather.test": {"forecast": result.get("rows", [])}}

        hass.services.async_register("select", "select_option", select)
        result["select_handler"] = select
        hass.services.async_register("weather", "get_forecasts", forecast, supports_response=SupportsResponse.ONLY)
        yield result
        result["controller"].close()
        await hass.async_stop()


async def run(env, **changes):
    return await env["controller"].async_evaluate({**CONFIG, **changes})


async def stable(env, **changes):
    await run(env, **changes)
    await run(env, **changes)


def temperature(env, value, unit="°C"):
    env["hass"].states.async_set("sensor.outside", str(value), {"unit_of_measurement": unit})


async def restart(env):
    old = env["controller"]
    old.close()
    env["controller"] = ComfortRules(env["hass"])
    await env["controller"].async_load()
    return env["controller"]


@pytest.mark.parametrize(("value", "expected"), [(4.9, 1), (5, 0), (7, 0), ("unknown", 0), ("nan", 0), ("unavailable", 0)])
async def test_cold_start_is_strict_and_missing_is_not_zero(env, value, expected):
    temperature(env, value)
    await stable(env)
    assert len(env["calls"]) == expected


async def test_full_cycle_warm_stop_then_cold_restart_only_after_pause(env):
    await stable(env)
    temperature(env, 6.9)
    await stable(env)
    assert [option for _, option in env["calls"]] == ["level_1"]
    temperature(env, 7)
    await stable(env)
    assert [option for _, option in env["calls"]] == ["level_1", "off"]
    temperature(env, -2)
    env["clock"].tick(6 * 3600 - 1)
    await stable(env)
    assert len(env["calls"]) == 2
    env["clock"].tick(1)
    await stable(env)
    assert [option for _, option in env["calls"]] == ["level_1", "off", "level_1"]


async def test_maximum_stops_even_with_unknown_temperature(env):
    await stable(env)
    temperature(env, "unavailable")
    env["clock"].tick(4 * 3600)
    await env["controller"].async_deadlines()
    assert env["calls"][-1][1] == "off"
    await env["controller"].async_deadlines()
    assert env["controller"].data["devices"]["select.room"]["phase"] == "cooldown"


async def test_restart_keeps_original_deadline_and_cooldown(env):
    await stable(env)
    deadline = env["controller"].data["devices"]["select.room"]["deadline"]
    env["clock"].tick(3 * 3600)
    controller = await restart(env)
    await stable(env)
    assert controller.data["devices"]["select.room"]["deadline"] == deadline
    env["clock"].tick(3600)
    await controller.async_deadlines()
    await controller.async_deadlines()
    next_start = controller.data["devices"]["select.room"]["restart_after"]
    await restart(env)
    assert env["controller"].data["devices"]["select.room"]["restart_after"] == next_start
    await stable(env)
    assert len(env["calls"]) == 2


async def test_overdue_restart_sends_off_when_entity_returns(env):
    await stable(env)
    env["hass"].states.async_set("select.room", "unavailable", {"options": OPTIONS})
    env["clock"].tick(5 * 3600)
    controller = await restart(env)
    await controller.async_deadlines()
    assert len(env["calls"]) == 1
    env["hass"].states.async_set("select.room", "level_1", {"options": OPTIONS})
    await controller.async_deadlines()
    assert env["calls"][-1][1] == "off"


@pytest.mark.parametrize("change", [{"use_stop_temperature": False}, {"use_max_runtime": False}])
async def test_either_stop_mechanism_can_be_used_alone(env, change):
    await stable(env, **change)
    temperature(env, 8)
    await stable(env, **change)
    assert env["hass"].states.get("select.room").state == ("level_1" if not change.get("use_stop_temperature", True) else "off")


@pytest.mark.parametrize("change", [
    {"use_stop_temperature": False, "use_max_runtime": False}, {"stop_at": 5}, {"stop_at": 4},
    {"source_mode": "forecast"}, {"rule_id": "sensor.not_rule"},
])
async def test_invalid_rule_never_dispatches(env, change):
    with pytest.raises(ServiceValidationError):
        await run(env, **change)
    assert env["calls"] == []


async def test_repeated_evaluations_do_not_extend_run_or_repeat_write(env):
    await stable(env)
    deadline = env["controller"].data["devices"]["select.room"]["deadline"]
    for _ in range(10):
        env["clock"].tick(60)
        await run(env)
    assert len(env["calls"]) == 1
    assert env["controller"].data["devices"]["select.room"]["deadline"] == deadline


async def test_manual_change_is_not_overwritten(env):
    await stable(env)
    env["hass"].states.async_set("select.room", "level_3", {"options": OPTIONS})
    await stable(env)
    env["clock"].tick(7 * 3600)
    await stable(env)
    assert len(env["calls"]) == 1
    assert env["hass"].states.get("select.room").state == "level_3"


async def test_manually_active_room_is_not_adopted(env):
    env["hass"].states.async_set("select.room", "level_1", {"options": OPTIONS})
    await stable(env)
    assert env["calls"] == []
    assert env["controller"].data["devices"] == {}


async def test_disabled_automation_cannot_start_but_existing_maximum_still_stops(env):
    env["hass"].states.async_set("automation.rule", "off")
    await run(env)
    assert env["calls"] == []
    env["hass"].states.async_set("automation.rule", "on")
    await stable(env)
    env["hass"].states.async_set("automation.rule", "off")
    env["clock"].tick(4 * 3600)
    await env["controller"].async_deadlines()
    assert env["calls"][-1][1] == "off"


async def test_delayed_ha_state_does_not_cancel_confirmed_start_early(env):
    env["delay_state"] = True
    await stable(env)
    assert env["controller"].data["devices"]["select.room"]["phase"] == "starting"
    assert len(env["calls"]) == 1
    env["hass"].states.async_set("select.room", "level_1", {"options": OPTIONS})
    await stable(env)
    assert env["controller"].data["devices"]["select.room"]["phase"] == "running"


async def test_unconfirmed_start_survives_restart_without_replay(env):
    env["command_error"] = True
    with pytest.raises(HomeAssistantError):
        await run(env)
    await restart(env)
    await stable(env)
    assert len(env["calls"]) == 1
    assert env["controller"].data["devices"]["select.room"]["phase"] == "uncertain_start"
    await env["controller"].async_reset("automation.rule")
    assert env["controller"].data["devices"]["select.room"]["phase"] == "cooldown"


async def test_unconfirmed_stop_is_resolved_from_off_without_replay(env):
    await stable(env)
    env["command_error"] = True
    env["clock"].tick(4 * 3600)
    await env["controller"].async_deadlines()
    await env["controller"].async_deadlines()
    assert len(env["calls"]) == 2
    with pytest.raises(ServiceValidationError):
        await env["controller"].async_reset("automation.rule")
    env["hass"].states.async_set("select.room", "off", {"options": OPTIONS})
    await env["controller"].async_deadlines()
    assert env["controller"].data["devices"]["select.room"]["phase"] == "cooldown"


async def test_storage_failure_prevents_command(env, monkeypatch):
    def fail(*_):
        raise OSError("disk full")
    monkeypatch.setattr(module, "_save", fail)
    with pytest.raises(HomeAssistantError):
        await run(env)
    assert env["calls"] == []


async def test_corrupt_storage_blocks_rules_not_the_hvac_integration(env):
    Path(env["controller"].path).parent.mkdir(parents=True, exist_ok=True)
    Path(env["controller"].path).write_text('{"broken":true}', encoding="utf-8")
    await restart(env)
    with pytest.raises(HomeAssistantError):
        await run(env)
    assert env["calls"] == []


@pytest.mark.parametrize("unit", ["°C", "°F"])
async def test_current_weather_and_fahrenheit(env, unit):
    temperature(env, 39.2 if unit == "°F" else 4, unit)
    await stable(env)
    assert len(env["calls"]) == 1


async def test_forecast_minimum_looks_forward_and_is_cached(env):
    env["rows"] = [{"datetime": (NOW + timedelta(hours=i)).isoformat(), "temperature": 3 if i == 8 else 10} for i in range(1, 25)]
    await stable(env, source="weather.test", source_mode="forecast")
    assert len(env["calls"]) == 1
    assert env["forecast_calls"] == 1
    env["clock"].tick(9 * 3600)
    await stable(env, source="weather.test", source_mode="forecast")
    assert env["calls"][-1][1] == "off"


@pytest.mark.parametrize("rows", [[], [{"datetime": NOW.isoformat(), "temperature": -10}], [{"datetime": "bad", "temperature": -10}]])
async def test_incomplete_forecast_does_not_start(env, rows):
    env["rows"] = rows
    await stable(env, source="weather.test", source_mode="forecast")
    assert env["calls"] == []


async def test_non_salus_target_cannot_be_controlled(env):
    er.async_get(env["hass"]).async_get_or_create("select", "other", "fake", suggested_object_id="other")
    env["hass"].states.async_set("select.other", "off", {"options": OPTIONS})
    with pytest.raises(ServiceValidationError):
        await run(env, floor_entities=["select.other"])
    assert env["calls"] == []


async def test_one_uncertain_room_does_not_block_other_room_deadline(env):
    hass = env["hass"]
    er.async_get(hass).async_get_or_create("select", "salus", "second_comfort_warm_floor", suggested_object_id="second")
    hass.states.async_set("select.second", "off", {"options": OPTIONS})
    await stable(env, floor_entities=["select.room", "select.second"])
    original = env["select_handler"]

    async def partially_failed(call):
        if call.data["entity_id"] == "select.room":
            raise HomeAssistantError("only first room failed")
        await original(call)

    hass.services.async_register("select", "select_option", partially_failed)
    env["clock"].tick(4 * 3600)
    await env["controller"].async_deadlines()
    assert hass.states.get("select.second").state == "off"
    assert env["controller"].data["devices"]["select.room"]["phase"] == "uncertain_stop"


async def test_forecast_failure_does_not_block_maximum_runtime(env):
    env["rows"] = [{"datetime": (NOW + timedelta(hours=i)).isoformat(), "temperature": 3} for i in range(1, 25)]
    await stable(env, source="weather.test", source_mode="forecast")
    env["forecast_error"] = True
    env["clock"].tick(4 * 3600)
    await run(env, source="weather.test", source_mode="forecast")
    assert env["calls"][-1] == ("select.room", "off")


async def test_blueprint_has_help_for_every_input_and_valid_actions(env):
    path = Path(__file__).resolve().parents[1] / "blueprints/automation/salus_comfort_rule.yaml"
    blueprint = Blueprint(yaml_util.load_yaml_dict(str(path)), expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA)
    assert all(len(item["description"]) > 60 for item in blueprint.inputs.values())
    inputs = BlueprintInputs(blueprint, {"use_blueprint": {"path": str(path), "input": {"floor_entities": ["select.room"], "source": "sensor.outside"}}})
    inputs.validate()
    assert PLATFORM_SCHEMA(inputs.async_substitute())


async def test_services_register_once_without_gateway_traffic(env):
    await async_setup_comfort_rules(env["hass"])
    await async_setup_comfort_rules(env["hass"])
    assert env["hass"].services.has_service("salus", "evaluate_comfort_rule")
    assert env["calls"] == []


def test_load_rejects_nonfinite_deadline(tmp_path):
    config = _config(CONFIG)
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"version": 1, "rules": {"automation.rule": config}, "devices": {"select.room": {"owner": "automation.rule", "phase": "running", "level": "level_1", "started_at": 1, "cooldown_hours": 6, "settle_until": 1, "deadline": float("nan")}}}), encoding="utf-8")
    with pytest.raises(vol.Invalid):
        _load(str(path))


async def test_result_explains_start_and_next_tick_without_new_command(env):
    first = await run(env)
    deadline = first["rooms"]["select.room"]["maximum_stop_at"]
    assert first["temperature_c"] == 4
    assert first["rooms"]["select.room"]["decision"] == "started"
    assert first["rooms"]["select.room"]["command"] == "level_1"
    env["clock"].tick(60)
    second = await run(env)
    assert second["rooms"]["select.room"]["decision"] == "continue"
    assert second["rooms"]["select.room"]["command"] is None
    assert second["rooms"]["select.room"]["maximum_stop_at"] == deadline
    assert len(env["calls"]) == 1
    assert env["controller"]._evaluation is None


async def test_result_distinguishes_cold_threshold_missing_data_and_manual_level(env):
    temperature(env, 6)
    result = await run(env)
    assert result["rooms"]["select.room"]["decision"] == "not_cold_enough"
    temperature(env, "unavailable")
    result = await run(env)
    assert result["temperature_c"] is None
    assert result["temperature_data"]["status"] == "unavailable"
    assert result["rooms"]["select.room"]["decision"] == "missing_temperature"
    env["hass"].states.async_set("select.room", "level_2", {"options": OPTIONS})
    result = await run(env)
    assert result["rooms"]["select.room"]["decision"] == "manual_level"
    assert not env["calls"]


async def test_result_explains_warm_stop_then_pause_and_restart(env):
    await stable(env)
    temperature(env, 7)
    stopped = await run(env)
    room = stopped["rooms"]["select.room"]
    assert room["decision"] == "stopped"
    assert "slukgrænsen" in room["explanation"]
    assert room["command"] == "off"
    temperature(env, 4)
    paused = await run(env)
    assert paused["rooms"]["select.room"]["decision"] == "cooldown"
    assert paused["rooms"]["select.room"]["next_start_not_before"]
    await restart(env)
    again = await run(env)
    assert again["rooms"]["select.room"]["next_start_not_before"] == paused["rooms"]["select.room"]["next_start_not_before"]


async def test_result_retains_maximum_stop_when_first_pass_already_sent_off(env):
    await stable(env)
    env["clock"].tick(4 * 3600)
    temperature(env, "unavailable")
    result = await run(env)
    assert result["rooms"]["select.room"]["decision"] == "stopped"
    assert "Maksimal køretid" in result["rooms"]["select.room"]["explanation"]
    assert result["rooms"]["select.room"]["command"] == "off"
    json.dumps(result, allow_nan=False)


async def test_result_forecast_minimum_timestamp_and_cache_are_the_actual_values(env):
    env["rows"] = [{"datetime": (NOW + timedelta(hours=i)).isoformat(), "temperature": 2 if i == 6 else 10} for i in range(1, 25)]
    result = await run(env, source="weather.test", source_mode="forecast", forecast_hours=8, use_max_runtime=False)
    assert result["temperature_c"] == 2
    assert result["temperature_data"]["valid_points"] == 8
    assert datetime.fromisoformat(result["temperature_data"]["minimum_at"]) == NOW + timedelta(hours=6)
    assert not result["temperature_data"]["from_cache"]
    assert result["rooms"]["select.room"]["maximum_stop_at"] is None
    cached = await run(env, source="weather.test", source_mode="forecast", forecast_hours=8, use_max_runtime=False)
    assert cached["temperature_data"]["from_cache"]
    assert env["forecast_calls"] == 1


@pytest.mark.parametrize("provider_error", [False, True])
async def test_result_explains_incomplete_forecast_and_provider_error(env, provider_error):
    env["forecast_error"] = provider_error
    result = await run(env, source="weather.test", source_mode="forecast")
    assert result["temperature_data"]["status"] == ("forecast_error" if provider_error else "invalid_forecast")
    assert result["temperature_c"] is None
    assert env["calls"] == []


async def test_result_distinguishes_unavailable_room_and_disabled_automation(env):
    env["hass"].states.async_set("select.room", "unavailable")
    result = await run(env)
    assert result["rooms"]["select.room"]["decision"] == "unavailable"
    env["hass"].states.async_set("select.room", "off", {"options": OPTIONS})
    env["hass"].states.async_set("automation.rule", "off")
    result = await run(env)
    assert result["rooms"]["select.room"]["decision"] == "disabled"
    assert result["temperature_data"]["status"] == "not_evaluated"
    assert not env["calls"]


async def test_actual_blueprint_returns_visible_trace_variables_and_old_calls_work(env):
    hass = env["hass"]
    await async_setup_comfort_rules(hass)
    controller = hass.data["salus_comfort_rules"]
    try:
        # Existing b9 blueprints do not request a response and must keep working.
        await hass.services.async_call("salus", "evaluate_comfort_rule", CONFIG, blocking=True)
        path = Path(__file__).resolve().parents[1] / "blueprints/automation/salus_comfort_rule.yaml"
        blueprint = Blueprint(yaml_util.load_yaml_dict(str(path)), expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA)
        inputs = BlueprintInputs(blueprint, {"use_blueprint": {"path": str(path), "input": {"floor_entities": ["select.room"], "source": "sensor.outside"}}})
        config = inputs.async_substitute()
        script = Script(hass, cv.SCRIPT_SCHEMA(config.get("actions", config.get("action"))), "SALUS trace test", "salus")
        trace_get(clear=True)
        result = await script.async_run({"this": {"entity_id": "automation.rule"}}, context=Context())
        assert result.variables["temperaturgrundlag_c"] == 4
        assert "fortsætter" in result.variables["forklaring"]
        assert result.variables["rum_og_timer"]["select.room"]["maximum_stop_at"]
        assert result.variables["vejrdata"]["status"] == "valid"
        final_step = trace_get(clear=False)["1"][-1].as_dict()
        assert "fortsætter" in final_step["changed_variables"]["forklaring"]
        assert final_step["changed_variables"]["temperaturgrundlag_c"] == 4
        assert "rum_og_timer" in final_step["changed_variables"]
        assert len(env["calls"]) == 1
    finally:
        controller.close()


def hourly_forecast(env, temperature=2):
    env["rows"] = [{"datetime": (NOW + timedelta(hours=i)).isoformat(), "temperature": temperature} for i in range(1, 25)]


async def test_forecast_starts_but_current_weather_stops_even_while_forecast_is_cold(env):
    hourly_forecast(env)
    await stable(env, source="weather.test", source_mode="forecast")
    env["hass"].states.async_set("weather.test", "cloudy", {"temperature": 7, "temperature_unit": "°C"})
    result = await run(env, source="weather.test", source_mode="forecast")
    assert result["temperature_c"] == 2
    assert result["stop_temperature_c"] == 7
    assert result["rooms"]["select.room"]["decision"] == "stopped"
    assert "aktuelle udetemperatur" in result["rooms"]["select.room"]["explanation"]
    assert env["calls"] == [("select.room", "level_1"), ("select.room", "off")]


async def test_warm_future_does_not_stop_when_current_weather_is_still_cold(env):
    hourly_forecast(env)
    await stable(env, source="weather.test", source_mode="forecast", use_max_runtime=False)
    env["clock"].tick(16 * 60)
    hourly_forecast(env, 10)
    result = await run(env, source="weather.test", source_mode="forecast", use_max_runtime=False)
    assert result["temperature_c"] == 10
    assert result["stop_temperature_c"] == 4
    assert result["rooms"]["select.room"]["decision"] == "continue"
    assert len(env["calls"]) == 1


async def test_warm_current_stops_before_a_failed_forecast_request(env):
    hourly_forecast(env)
    await stable(env, source="weather.test", source_mode="forecast")
    env["clock"].tick(16 * 60)
    env["hass"].states.async_set("weather.test", "cloudy", {"temperature": 8, "temperature_unit": "°C"})

    async def unavailable_forecast(call):
        assert env["hass"].states.get("select.room").state == "off"
        raise HomeAssistantError("provider unavailable")

    env["hass"].services.async_register("weather", "get_forecasts", unavailable_forecast, supports_response=SupportsResponse.ONLY)
    result = await run(env, source="weather.test", source_mode="forecast")
    assert result["temperature_c"] is None
    assert result["stop_temperature_c"] == 8
    assert result["rooms"]["select.room"]["decision"] == "stopped"


async def test_missing_current_temperature_does_not_use_warm_forecast_as_stop(env):
    hourly_forecast(env)
    await stable(env, source="weather.test", source_mode="forecast")
    env["clock"].tick(16 * 60)
    hourly_forecast(env, 10)
    env["hass"].states.async_set("weather.test", "cloudy", {"temperature_unit": "°C"})
    result = await run(env, source="weather.test", source_mode="forecast")
    assert result["temperature_c"] == 10
    assert result["stop_temperature_c"] is None
    assert result["current_temperature_data"]["status"] == "invalid"
    assert len(env["calls"]) == 1


@pytest.mark.parametrize("temperature_stop", [True, False])
async def test_warm_current_has_priority_only_when_temperature_stop_is_enabled(env, temperature_stop):
    hourly_forecast(env)
    env["hass"].states.async_set("weather.test", "cloudy", {"temperature": 8, "temperature_unit": "°C"})
    result = await run(env, source="weather.test", source_mode="forecast", use_stop_temperature=temperature_stop)
    assert result["rooms"]["select.room"]["decision"] == ("warm_now" if temperature_stop else "started")
    assert len(env["calls"]) == (0 if temperature_stop else 1)


async def test_current_weather_fahrenheit_is_used_for_stop_independently(env):
    hourly_forecast(env, 35.6)  # 2°C, with this weather entity displaying Fahrenheit.
    env["hass"].states.async_set("weather.test", "cloudy", {"temperature": 39.2, "temperature_unit": "°F"})
    await stable(env, source="weather.test", source_mode="forecast")
    env["hass"].states.async_set("weather.test", "cloudy", {"temperature": 46.4, "temperature_unit": "°F"})
    result = await run(env, source="weather.test", source_mode="forecast")
    assert result["temperature_c"] == pytest.approx(2)
    assert result["stop_temperature_c"] == pytest.approx(8)
    assert env["calls"][-1][1] == "off"
