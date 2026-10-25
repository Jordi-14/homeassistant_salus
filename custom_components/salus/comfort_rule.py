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
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er, issue_registry as ir
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.start import async_at_start
from homeassistant.util.file import write_utf8_file_atomic

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

    async def _temperature(self, config: dict) -> float | None:
        source = self.hass.states.get(config["source"])
        if source is None or source.state in ("unavailable", "unknown"):
            return None
        unit = source.attributes.get("temperature_unit" if config["source"].startswith("weather.") else "unit_of_measurement")
        if config["source_mode"] == "current":
            return _celsius(source.attributes.get("temperature") if config["source"].startswith("weather.") else source.state, unit)
        now = self._now()
        cached = self.cache.get(config["source"])
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
                return None
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
        if len(points) < math.ceil(config["forecast_hours"]) or len({p[0] for p in points}) != len(points):
            return None
        if points[0][0] > now + 3600 or points[-1][0] < end - 3600 or any(b[0] - a[0] > 3601 for a, b in zip(points, points[1:], strict=False)):
            return None
        return min(p[1] for p in points)

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

    async def _advance(self, entity: str, record: dict, config: dict, temperature: float | None, *, allow_start: bool) -> None:
        now = self._now()
        current = self._floor(entity)
        if current is None:
            return
        phase = record["phase"]
        if phase in ("stopping", "uncertain_stop"):
            if current == "off":
                await self._cooldown(entity, record)
            # Never replay an uncertain stop. A repair remains until read-back
            # confirms Off, or the user sets Off and resets the rule.
            return
        if phase in ("starting", "uncertain_start"):
            if current == record["level"]:
                record["phase"] = "running"
                await self._persist()
            elif current == "off" and record.get("confirmed") and now >= record["settle_until"]:
                await self._cooldown(entity, record)
                return
            else:
                return
        if record["phase"] == "running":
            if current != record["level"]:
                # A manual change relinquishes ownership, never overwrites it.
                await self._cooldown(entity, record)
                return
            expired = record.get("deadline") is not None and now >= record["deadline"]
            warm = temperature is not None and config["use_stop_temperature"] and temperature >= config["stop_at"]
            removed = entity not in config["floor_entities"]
            if expired or warm or removed:
                record.update(phase="stopping", confirmed=False, settle_until=now + 30)
                await self._command(entity, "off", record)
            return
        if record["phase"] == "cooldown" and now >= record["restart_after"] and allow_start and current == "off" and temperature is not None and temperature < config["start_below"]:
            await self._start(entity, config)

    async def _start(self, entity: str, config: dict) -> None:
        now = self._now()
        record = {"owner": config["rule_id"], "phase": "starting", "level": config["level"], "started_at": now,
                  "deadline": now + config["max_runtime_hours"] * 3600 if config["use_max_runtime"] else None,
                  "cooldown_hours": config["cooldown_hours"], "restart_after": None, "confirmed": False, "settle_until": now + 30}
        self.data["devices"][entity] = record
        await self._command(entity, config["level"], record)

    async def async_evaluate(self, raw: dict) -> None:
        config = _config(raw)
        async with self.lock:
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
                temperature = await self._temperature(config) if enabled else None
                for entity in config["floor_entities"]:
                    record = self.data["devices"].get(entity)
                    if record is not None:
                        if record["owner"] == config["rule_id"]:
                            await self._advance(entity, record, config, temperature, allow_start=enabled)
                        elif record["phase"] == "cooldown" and self._now() >= record["restart_after"] and enabled:
                            previous = self.hass.states.get(record["owner"])
                            if (previous is None or previous.state != "on") and temperature is not None and temperature < config["start_below"] and self._floor(entity) == "off":
                                await self._start(entity, config)
                    elif enabled and temperature is not None and temperature < config["start_below"] and self._floor(entity) == "off":
                        await self._start(entity, config)
            finally:
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

    async def evaluate(call: ServiceCall) -> None:
        await controller.async_evaluate(dict(call.data))

    async def reset(call: ServiceCall) -> None:
        await controller.async_reset(call.data["rule_id"])

    hass.services.async_register(DOMAIN, "evaluate_comfort_rule", evaluate, schema=RULE_SCHEMA)
    hass.services.async_register(DOMAIN, "reset_comfort_rule", reset, schema=vol.Schema({vol.Required("rule_id"): cv.entity_id}))
    async_at_start(hass, controller.async_deadlines)
    hass.bus.async_listen_once("homeassistant_stop", controller.close)
