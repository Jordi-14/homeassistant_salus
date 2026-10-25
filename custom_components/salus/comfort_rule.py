"""Persistent single-rule comfort cycles; all writes use the normal select path."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er, issue_registry as ir
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.start import async_at_start
from homeassistant.util.file import write_utf8_file_atomic
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
_KEY = "salus_comfort_rules"
_OPTIONS = ("off", "level_1", "level_2", "level_3")
_PHASES = {"starting", "running", "stopping", "uncertain_start", "uncertain_stop", "cooldown"}


def _number(value: Any) -> float:
    if isinstance(value, bool):
        raise vol.Invalid("expected a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise vol.Invalid("expected a finite number") from error
    if not math.isfinite(result):
        raise vol.Invalid("expected a finite number")
    return result


RULE_SCHEMA = vol.Schema({
    vol.Required("rule_id"): cv.entity_id,
    vol.Required("floor_entities"): vol.All(cv.entity_ids, vol.Length(min=1, max=50)),
    vol.Required("source"): cv.entity_id,
    vol.Optional("source_mode", default="current"): vol.In(("current", "forecast")),
    vol.Optional("forecast_hours", default=12): vol.All(_number, vol.Range(min=1, max=48)),
    vol.Optional("level", default="level_1"): vol.In(_OPTIONS[1:]),
    vol.Optional("start_below", default=5): vol.All(_number, vol.Range(min=-50, max=50)),
    vol.Optional("use_stop_temperature", default=True): cv.boolean,
    vol.Optional("stop_at", default=7): vol.All(_number, vol.Range(min=-50, max=60)),
    vol.Optional("use_max_runtime", default=True): cv.boolean,
    vol.Optional("max_runtime_hours", default=4): vol.All(_number, vol.Range(min=.25, max=168)),
    vol.Optional("cooldown_hours", default=6): vol.All(_number, vol.Range(min=0, max=168)),
})


def _config(data: dict) -> dict:
    config = RULE_SCHEMA(data)
    if not config["rule_id"].startswith("automation."):
        raise ServiceValidationError("Reglen skal tilhøre en automation.")
    if not config["source"].startswith(("sensor.", "weather.")):
        raise ServiceValidationError("Vælg en temperaturføler eller vejrudsigt.")
    if config["source_mode"] == "forecast" and not config["source"].startswith("weather."):
        raise ServiceValidationError("Prognose kræver en weather-entitet.")
    if not config["use_stop_temperature"] and not config["use_max_runtime"]:
        raise ServiceValidationError("Vælg mindst én slukbetingelse: temperatur eller maksimal køretid.")
    if config["use_stop_temperature"] and config["stop_at"] <= config["start_below"]:
        raise ServiceValidationError("Slukgrænsen skal være højere end tændgrænsen.")
    config["floor_entities"] = list(dict.fromkeys(config["floor_entities"]))
    return config


def _load(path: str) -> dict:
    target = Path(path)
    if not target.exists():
        return {"version": 1, "rules": {}, "devices": {}}
    data = json.loads(target.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("rules"), dict) or not isinstance(data.get("devices"), dict):
        raise ValueError("Invalid comfort-rule storage")
    for key, config in data["rules"].items():
        normalized = _config(config)
        if normalized["rule_id"] != key:
            raise ValueError("Invalid stored rule identity")
        data["rules"][key] = normalized
    for entity, record in data["devices"].items():
        if not entity.startswith("select.") or record.get("owner") not in data["rules"] or record.get("phase") not in _PHASES or record.get("level") not in _OPTIONS[1:]:
            raise ValueError("Invalid stored comfort cycle")
        for key in ("started_at", "cooldown_hours", "settle_until"):
            _number(record[key])
        for key in ("deadline", "restart_after"):
            if record.get(key) is not None:
                _number(record[key])
    return data


def _save(path: str, data: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    write_utf8_file_atomic(path, json.dumps(data, ensure_ascii=True), private=True)
    if json.loads(Path(path).read_text(encoding="utf-8")) != data:
        raise OSError("Comfort-rule state did not match saved data")


def _celsius(value: Any, unit: str | None) -> float | None:
    try:
        number = _number(value)
    except vol.Invalid:
        return None
    if unit == "°C":
        return number
    if unit == "°F":
        return (number - 32) * 5 / 9
    return None


class ComfortRules:
    """One serialized controller shared by blueprints, with restart-safe cycles."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.path = hass.config.path(".storage", "salus_comfort_rules.json")
        self.data: dict = {"version": 1, "rules": {}, "devices": {}}
        self.lock = asyncio.Lock()
        self.cache: dict = {}
        self.load_error: str | None = None
        self._cancel = None
        self._evaluation: dict | None = None

    def _time(self, stamp: float | None) -> str | None:
        return dt_util.as_local(datetime.fromtimestamp(stamp, UTC)).isoformat() if stamp is not None else None

    def _explain(self, entity: str, decision: str, explanation: str, command: str | None = None) -> None:
        """Record decisions in memory only, without changing the control path."""
        if self._evaluation is None:
            return
        rooms = self._evaluation["rooms"]
        if entity in rooms and rooms[entity].get("command") and command is None:
            return  # Keep the command that was actually sent in the first pass.
        if entity in rooms and rooms[entity]["decision"] == "manual_change" and decision == "cooldown":
            return
        rooms[entity] = {"decision": decision, "explanation": explanation, "command": command}

    def _now(self) -> float:
        return datetime.now(UTC).timestamp()

    async def async_load(self) -> None:
        try:
            self.data = await self.hass.async_add_executor_job(_load, self.path)
        except Exception as error:
            self.load_error = str(error)
            _LOGGER.error("Comfort automation storage cannot be loaded; automatic commands blocked: %s", error)

    async def _persist(self) -> None:
        if self.load_error:
            raise HomeAssistantError("Komfortreglernes lager kan ikke læses; automatisk styring er blokeret.")
        try:
            await self.hass.async_add_executor_job(_save, self.path, copy.deepcopy(self.data))
        except Exception as error:
            raise HomeAssistantError("Komfortreglens timer kunne ikke gemmes; ingen ny kommando sendes.") from error

    def _floor(self, entity: str) -> str | None:
        entry = er.async_get(self.hass).async_get(entity)
        if entry is None or entry.platform != DOMAIN or not entry.unique_id.endswith("_comfort_warm_floor"):
            raise ServiceValidationError(f"{entity} er ikke en SALUS Gulvkomfort-entitet.")
        state = self.hass.states.get(entity)
        if state is None or state.state not in _OPTIONS or not all(option in state.attributes.get("options", []) for option in _OPTIONS):
            return None
        return state.state

    def _current_temperature(self, config: dict) -> tuple[float | None, dict]:
        """Stop against the actual current outdoor value, never a future minimum."""
        source = self.hass.states.get(config["source"])
        detail = {"status": "unavailable", "source": config["source"], "explanation": "Aktuel udetemperatur mangler eller er utilgængelig; temperaturslukning afventer."}
        if source is None or source.state in ("unavailable", "unknown"):
            return None, detail
        weather = config["source"].startswith("weather.")
        value = _celsius(source.attributes.get("temperature") if weather else source.state,
                         source.attributes.get("temperature_unit" if weather else "unit_of_measurement"))
        detail.update(status="valid" if value is not None else "invalid", explanation="Aktuel udetemperatur nu fra vejrtjenesten eller udeføleren; bruges til slukgrænsen." if value is not None else "Aktuel udetemperatur eller enhed er ugyldig; temperaturslukning afventer.")
        return value, detail

    async def _temperature(self, config: dict) -> float | None:
        source = self.hass.states.get(config["source"])
        detail = {"status": "unavailable", "explanation": "Temperaturkilden mangler eller er utilgængelig."}
        if self._evaluation is not None:
            self._evaluation["temperature_data"] = detail
        if source is None or source.state in ("unavailable", "unknown"):
            return None
        unit = source.attributes.get("temperature_unit" if config["source"].startswith("weather.") else "unit_of_measurement")
        if config["source_mode"] == "current":
            value = _celsius(source.attributes.get("temperature") if config["source"].startswith("weather.") else source.state, unit)
            detail.update(status="valid" if value is not None else "invalid", explanation="Aktuel temperatur i Celsius." if value is not None else "Temperaturen eller temperaturenheden er ugyldig.")
            return value
        now = self._now()
        detail.update(status="invalid_forecast", explanation="Timeprognosen mangler gyldige, sammenhængende data for hele perioden.",
                      period_start=self._time(now), period_end=self._time(now + config["forecast_hours"] * 3600))
        cached = self.cache.get(config["source"])
        detail["from_cache"] = cached is not None and now - cached["fetched_at"] < 900
        if cached is None or now - cached["fetched_at"] >= 900:
            try:
                async with asyncio.timeout(10):
                    response = await self.hass.services.async_call("weather", "get_forecasts", {"entity_id": config["source"], "type": "hourly"}, blocking=True, return_response=True)
                rows = response[config["source"]]["forecast"]
                if not isinstance(rows, list):
                    return None
                cached = {"fetched_at": now, "rows": rows}
                self.cache[config["source"]] = cached
            except (HomeAssistantError, KeyError, TypeError, TimeoutError):
                detail.update(status="forecast_error", explanation="Timeprognosen kunne ikke hentes fra vejrtjenesten.")
                return None
        detail["fetched_at"] = self._time(cached["fetched_at"])
        points = []
        end = now + config["forecast_hours"] * 3600
        for row in cached["rows"]:
            try:
                time = datetime.fromisoformat(str(row["datetime"]).replace("Z", "+00:00"))
                if time.tzinfo is None:
                    return None
                stamp = time.timestamp()
                if now <= stamp <= end:
                    value = _celsius(row.get("temperature"), unit)
                    if value is None:
                        return None
                    points.append((stamp, value))
            except (KeyError, TypeError, ValueError):
                return None
        points.sort()
        detail["valid_points"] = len(points)
        if len(points) < math.ceil(config["forecast_hours"]) or len({p[0] for p in points}) != len(points):
            return None
        if points[0][0] > now + 3600 or points[-1][0] < end - 3600 or any(b[0] - a[0] > 3601 for a, b in zip(points, points[1:], strict=False)):
            return None
        lowest = min(points, key=lambda point: point[1])
        detail.update(status="valid", explanation="Laveste timeprognose i den valgte periode, omregnet til Celsius.", minimum_at=self._time(lowest[0]))
        return lowest[1]

    async def _command(self, entity: str, option: str, record: dict) -> None:
        # The pending phase and original deadline reach disk BEFORE dispatch.
        await self._persist()
        try:
            await self.hass.services.async_call("select", "select_option", {"entity_id": entity, "option": option}, blocking=True)
        except Exception as error:
            record["phase"] = "uncertain_start" if option != "off" else "uncertain_stop"
            record["error"] = str(error)
            await self._persist()
            ir.async_create_issue(self.hass, DOMAIN, f"comfort_rule_{entity}", is_fixable=False, severity=ir.IssueSeverity.ERROR,
                                 translation_key="comfort_command_uncertain", translation_placeholders={"entity": entity})
            raise HomeAssistantError(f"Komfortkommando til {entity} er ikke bekræftet. Ingen automatisk genafsendelse.") from error
        record["confirmed"] = True
        record["settle_until"] = self._now() + 30
        await self._persist()

    async def _cooldown(self, entity: str, record: dict) -> None:
        record.update(phase="cooldown", restart_after=self._now() + record["cooldown_hours"] * 3600, deadline=None)
        await self._persist()
        ir.async_delete_issue(self.hass, DOMAIN, f"comfort_rule_{entity}")

    async def _advance(self, entity: str, record: dict, config: dict, temperature: float | None, *, allow_start: bool, stop_temperature: float | None = None) -> None:
        now = self._now()
        current = self._floor(entity)
        if current is None:
            self._explain(entity, "unavailable", "Rummets Gulvkomfort er utilgængelig; ingen kommando sendes.")
            return
        phase = record["phase"]
        if phase in ("stopping", "uncertain_stop"):
            if current == "off":
                await self._cooldown(entity, record)
                self._explain(entity, "cooldown", "Fra er bekræftet; minimumspausen er startet.")
            else:
                self._explain(entity, "awaiting_stop", "Afventer bekræftet Fra. En usikker slukkommando genafsendes ikke automatisk.")
            # Never replay an uncertain stop. A repair remains until read-back
            # confirms Off, or the user sets Off and resets the rule.
            return
        if phase in ("starting", "uncertain_start"):
            if current == record["level"]:
                record["phase"] = "running"
                await self._persist()
            elif current == "off" and record.get("confirmed") and now >= record["settle_until"]:
                await self._cooldown(entity, record)
                self._explain(entity, "cooldown", "Rummet melder Fra efter start; minimumspausen er startet.")
                return
            else:
                self._explain(entity, "awaiting_start", "Afventer det valgte niveau fra enheden; ingen ny tændkommando sendes.")
                return
        if record["phase"] == "running":
            if current != record["level"]:
                # A manual change relinquishes ownership, never overwrites it.
                await self._cooldown(entity, record)
                self._explain(entity, "manual_change", "En manuel ændring respekteres; automatisk styring venter og starter pausen.")
                return
            expired = record.get("deadline") is not None and now >= record["deadline"]
            warm = self._warm_now(config, stop_temperature)
            removed = entity not in config["floor_entities"]
            if expired or warm or removed:
                reason = "Maksimal køretid er udløbet." if expired else "Den aktuelle udetemperatur har nået slukgrænsen." if warm else "Rummet er fjernet fra reglen."
                self._explain(entity, "stopped", reason + " Gulvkomfort sættes til Fra.", "off")
                record.update(phase="stopping", confirmed=False, settle_until=now + 30)
                await self._command(entity, "off", record)
            else:
                self._explain(entity, "continue", "Komforten fortsætter; ingen slukbetingelse er nået, og ingen ny kommando sendes." if stop_temperature is not None else "Komforten fortsætter uden gyldig aktuel udetemperatur; en gemt maksimal køretid gælder stadig.")
            return
        if record["phase"] == "cooldown" and now >= record["restart_after"] and allow_start and current == "off" and temperature is not None and temperature < config["start_below"] and not self._warm_now(config, stop_temperature):
            await self._start(entity, config)
        elif record["phase"] == "cooldown":
            if now < record["restart_after"]:
                self._explain(entity, "cooldown", "Minimumspausen er ikke udløbet; ny start er blokeret.")
            else:
                self._waiting(entity, config, current, temperature, allow_start, stop_temperature)

    def _warm_now(self, config: dict, value: float | None) -> bool:
        return config["use_stop_temperature"] and value is not None and value >= config["stop_at"]

    def _waiting(self, entity: str, config: dict, current: str | None, temperature: float | None, enabled: bool, stop_temperature: float | None = None) -> None:
        if current is None:
            self._explain(entity, "unavailable", "Rummets Gulvkomfort er utilgængelig; ingen kommando sendes.")
        elif not enabled:
            self._explain(entity, "disabled", "Automationen er deaktiveret; ingen ny start tillades.")
        elif current != "off":
            self._explain(entity, "manual_level", "Komforten er allerede tændt manuelt og overtages ikke af reglen.")
        elif self._warm_now(config, stop_temperature):
            self._explain(entity, "warm_now", "Den aktuelle udetemperatur er ved eller over slukgrænsen; rummet forbliver Fra, selv om prognosen er kold.")
        elif temperature is None:
            self._explain(entity, "missing_temperature", "Der er ingen gyldig temperatur for perioden; rummet tændes ikke.")
        else:
            self._explain(entity, "not_cold_enough", "Temperaturgrundlaget er ikke under tændgrænsen; rummet forbliver Fra.")

    async def _start(self, entity: str, config: dict) -> None:
        now = self._now()
        record = {"owner": config["rule_id"], "phase": "starting", "level": config["level"], "started_at": now,
                  "deadline": now + config["max_runtime_hours"] * 3600 if config["use_max_runtime"] else None,
                  "cooldown_hours": config["cooldown_hours"], "restart_after": None, "confirmed": False, "settle_until": now + 30}
        self.data["devices"][entity] = record
        self._explain(entity, "started", "Temperaturgrundlaget er under tændgrænsen, rummet står på Fra, og ingen pause blokerer. Det valgte komfortniveau aktiveres.", config["level"])
        await self._command(entity, config["level"], record)

    async def async_evaluate(self, raw: dict) -> dict:
        config = _config(raw)
        async with self.lock:
            result = {"evaluated_at": self._time(self._now()), "rule_id": config["rule_id"], "source": config["source"],
                      "source_mode": config["source_mode"], "forecast_hours": config["forecast_hours"] if config["source_mode"] == "forecast" else None,
                      "temperature_c": None, "stop_temperature_c": None, "start_below_c": config["start_below"], "stop_at_c": config["stop_at"] if config["use_stop_temperature"] else None,
                      "max_runtime_enabled": config["use_max_runtime"], "rooms": {}}
            self._evaluation = result
            try:
                if self.load_error:
                    raise HomeAssistantError("Komfortreglernes lager er ugyldigt; styring er blokeret.")
                for entity in config["floor_entities"]:
                    self._floor(entity)
                if self.data["rules"].get(config["rule_id"]) != config:
                    self.data["rules"][config["rule_id"]] = config
                    await self._persist()
                owner = self.hass.states.get(config["rule_id"])
                enabled = owner is not None and owner.state == "on"
                # Always enforce existing maximum deadlines, even if the source
                # is offline or an upstream forecast request fails.
                for entity, record in list(self.data["devices"].items()):
                    if record["owner"] == config["rule_id"]:
                        await self._advance(entity, record, config, None, allow_start=False)
                stop_temperature, stop_data = self._current_temperature(config) if enabled else (None, {"status": "not_evaluated", "explanation": "Automationen er deaktiveret."})
                result["stop_temperature_c"] = stop_temperature
                result["current_temperature_data"] = stop_data
                # A warm-current stop does not depend on a valid forecast or on
                # waiting for the forecast provider to respond.
                if enabled:
                    for entity, record in list(self.data["devices"].items()):
                        if record["owner"] == config["rule_id"]:
                            await self._advance(entity, record, config, None, allow_start=False, stop_temperature=stop_temperature)
                temperature = await self._temperature(config) if enabled else None
                result["temperature_c"] = temperature
                result["automation_enabled"] = enabled
                if not enabled:
                    result["temperature_data"] = {"status": "not_evaluated", "explanation": "Automationen er deaktiveret; kun eksisterende slukfrister kontrolleres."}
                for entity in config["floor_entities"]:
                    record = self.data["devices"].get(entity)
                    if record is not None:
                        if record["owner"] == config["rule_id"]:
                            await self._advance(entity, record, config, temperature, allow_start=enabled, stop_temperature=stop_temperature)
                        elif record["phase"] == "cooldown" and self._now() >= record["restart_after"] and enabled:
                            previous = self.hass.states.get(record["owner"])
                            if (previous is None or previous.state != "on") and temperature is not None and temperature < config["start_below"] and self._floor(entity) == "off" and not self._warm_now(config, stop_temperature):
                                await self._start(entity, config)
                        if record["owner"] != config["rule_id"] and entity not in result["rooms"]:
                            self._explain(entity, "other_rule", "Rummet tilhører en anden komfortregel eller dennes pause; denne regel ændrer det ikke.")
                    elif enabled and temperature is not None and temperature < config["start_below"] and self._floor(entity) == "off" and not self._warm_now(config, stop_temperature):
                        await self._start(entity, config)
                    else:
                        self._waiting(entity, config, self._floor(entity), temperature, enabled, stop_temperature)
                for entity, item in result["rooms"].items():
                    record = self.data["devices"].get(entity, {})
                    state = self.hass.states.get(entity)
                    item.update(reported_level=state.state if state else None, phase=record.get("phase"),
                                started_at=self._time(record.get("started_at")), maximum_stop_at=self._time(record.get("deadline")),
                                next_start_not_before=self._time(record.get("restart_after")), owner=record.get("owner"))
                result["explanation"] = "Tændgrundlag: " + (f"{temperature:.2f} °C." if temperature is not None else "ingen gyldig temperatur.")
                result["explanation"] += " Udetemperatur nu (slukgrundlag): " + (f"{stop_temperature:.2f} °C." if stop_temperature is not None else "ingen gyldig aktuel udetemperatur.")
                result["explanation"] += " " + " ".join(f"{entity}: {item['explanation']}" for entity, item in result["rooms"].items())
                return result
            finally:
                self._evaluation = None
                self._schedule()

    @callback
    def _schedule(self) -> None:
        if self._cancel:
            self._cancel()
            self._cancel = None
        deadlines = [r["deadline"] for r in self.data["devices"].values() if r.get("deadline") is not None and r["phase"] != "cooldown"]
        if deadlines and not self.load_error:
            when = min(deadlines)
            if when <= self._now():
                when = self._now() + 30
            self._cancel = async_track_point_in_utc_time(self.hass, self.async_deadlines, datetime.fromtimestamp(when, UTC))

    async def async_deadlines(self, _event=None) -> None:
        async with self.lock:
            try:
                for entity, record in list(self.data["devices"].items()):
                    try:
                        await self._advance(entity, record, self.data["rules"][record["owner"]], None, allow_start=False)
                    except HomeAssistantError:
                        # An unconfirmed command for one room must not prevent
                        # another room's already committed deadline being checked.
                        _LOGGER.exception("Comfort rule deadline needs attention: %s", entity)
            finally:
                self._schedule()

    async def async_reset(self, rule_id: str) -> None:
        async with self.lock:
            records = {entity: record for entity, record in self.data["devices"].items() if record["owner"] == rule_id}
            if any(self._floor(entity) != "off" for entity in records):
                raise ServiceValidationError("Sæt alle regelstyrede Gulvkomfort-enheder til Fra før nulstilling.")
            for entity, record in records.items():
                await self._cooldown(entity, record)
            self._schedule()

    @callback
    def close(self, _event=None) -> None:
        if self._cancel:
            self._cancel()
            self._cancel = None


async def async_setup_comfort_rules(hass: HomeAssistant) -> None:
    if _KEY in hass.data:
        return
    controller = hass.data[_KEY] = ComfortRules(hass)
    await controller.async_load()

    async def evaluate(call: ServiceCall) -> dict:
        return await controller.async_evaluate(dict(call.data))

    async def reset(call: ServiceCall) -> None:
        await controller.async_reset(call.data["rule_id"])

    hass.services.async_register(DOMAIN, "evaluate_comfort_rule", evaluate, schema=RULE_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, "reset_comfort_rule", reset, schema=vol.Schema({vol.Required("rule_id"): cv.entity_id}))
    async_at_start(hass, controller.async_deadlines)
    hass.bus.async_listen_once("homeassistant_stop", controller.close)
