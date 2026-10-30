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
from homeassistant.components.logbook import async_log_entry
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er, issue_registry as ir
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.start import async_at_start
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util.file import write_utf8_file_atomic
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
_KEY = "salus_comfort_rules"
SIGNAL_COMFORT_STATUS = "salus_comfort_status"
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
    vol.Optional("cycle_mode", default="legacy_maximum"): vol.In(("legacy_maximum", "minimum")),
    vol.Optional("min_runtime_hours", default=4): vol.All(_number, vol.Range(min=.25, max=168)),
    vol.Optional("extension_hours", default=1): vol.All(_number, vol.Range(min=.25, max=24)),
    vol.Optional("outdoor_sensor", default=""): vol.Any("", cv.entity_id),
    vol.Optional("use_room_minimum", default=False): cv.boolean,
    vol.Optional("room_minimum", default=21): vol.All(_number, vol.Range(min=5, max=35)),
    vol.Optional("room_margin", default=.5): vol.All(_number, vol.Range(min=.1, max=5)),
    vol.Optional("adopt_manual", default=False): cv.boolean,
    vol.Optional("use_room_maximum", default=False): cv.boolean,
    vol.Optional("room_maximum", default=25): vol.All(_number, vol.Range(min=5, max=40)),
})


def _config(data: dict) -> dict:
    config = RULE_SCHEMA(data)
    if not config["rule_id"].startswith("automation."):
        raise ServiceValidationError("Reglen skal tilhøre en automation.")
    if not config["source"].startswith(("sensor.", "weather.")):
        raise ServiceValidationError("Vælg en temperaturføler eller vejrudsigt.")
    if config["source_mode"] == "forecast" and not config["source"].startswith("weather."):
        raise ServiceValidationError("Prognose kræver en weather-entitet.")
    if config["outdoor_sensor"] and not config["outdoor_sensor"].startswith("sensor."):
        raise ServiceValidationError("Udetemperaturføleren skal være en sensor-entitet.")
    if config["cycle_mode"] == "legacy_maximum" and not config["use_stop_temperature"] and not config["use_max_runtime"]:
        raise ServiceValidationError("Vælg mindst én slukbetingelse: temperatur eller maksimal køretid.")
    if (config["cycle_mode"] == "minimum" or config["use_stop_temperature"]) and config["stop_at"] <= config["start_below"]:
        raise ServiceValidationError("Slukgrænsen skal være højere end tændgrænsen.")
    if config["use_room_maximum"] and config["use_room_minimum"] and config["room_maximum"] <= config["room_minimum"] + config["room_margin"]:
        raise ServiceValidationError("Øvre rumgrænse skal være højere end rumminimum plus buffer.")
    if config["use_room_maximum"] and config["cycle_mode"] != "minimum":
        raise ServiceValidationError("Øvre rumgrænse kræver minimumperioder i den opdaterede blueprint.")
    config["floor_entities"] = list(dict.fromkeys(config["floor_entities"]))
    return config


def _load(path: str) -> dict:
    target = Path(path)
    if not target.exists():
        return {"version": 1, "rules": {}, "devices": {}}
    data = json.loads(target.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("rules"), dict) or not isinstance(data.get("devices"), dict):
        raise ValueError("Invalid comfort-rule storage")
    if not isinstance(data.get("observations", {}), dict):
        raise ValueError("Invalid comfort observations")
    for entity, observed in data.get("observations", {}).items():
        if not entity.startswith("select.") or not isinstance(observed, dict) or observed.get("level") not in _OPTIONS:
            raise ValueError("Invalid observed comfort state")
        for key in ("active_since", "last_off_at"):
            if observed.get(key) is not None:
                _number(observed[key])
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
        if record.get("cycle_mode") == "minimum":
            for key in ("minimum_until", "next_check_at", "active_at"):
                if record.get(key) is not None:
                    _number(record[key])
            for key in ("min_runtime_hours", "extension_hours"):
                if _number(record[key]) <= 0:
                    raise ValueError("Invalid saved comfort period")
            if type(record.get("room_hold")) is not bool or type(record.get("adopted")) is not bool:
                raise ValueError("Invalid per-room comfort state")
            if record["phase"] == "running" and (record.get("active_at") is None or record.get("minimum_until") is None or record.get("next_check_at") is None or record["next_check_at"] < record["minimum_until"]):
                raise ValueError("Invalid saved minimum-runtime deadline")
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
        self._cancel_room_listener = None
        self._closed = False

    @callback
    def watch_room_limits(self) -> None:
        """Act on new climate readings without waiting for a minute/period tick."""
        if self._closed or self._cancel_room_listener is not None:
            return

        @callback
        def changed(event) -> None:
            entity = event.data.get("entity_id", "")
            old, new = event.data.get("old_state"), event.data.get("new_state")
            if entity.startswith("automation.") and (old is None or new is None or old.state != new.state) and any(record["owner"] == entity for record in self.data["devices"].values()):
                async_dispatcher_send(self.hass, SIGNAL_COMFORT_STATUS)
                return
            if entity.startswith("select.") and new is not None and new.state in _OPTIONS and (old is None or old.state != new.state):
                entry = er.async_get(self.hass).async_get(entity)
                if entry is not None and entry.platform == DOMAIN and entry.unique_id.endswith("_comfort_warm_floor"):
                    self.hass.async_create_task(self.async_observe(entity, new.state, self._now()))
                return
            if not entity.startswith("climate."):
                return
            if new is None:
                return
            if old is not None and old.state == new.state and all(old.attributes.get(key) == new.attributes.get(key) for key in ("current_temperature", "temperature_unit")):
                return
            if any(self.data["rules"][record["owner"]].get("use_room_maximum") and record.get("cycle_mode") == "minimum" and record["phase"] in ("starting", "running") for record in self.data["devices"].values()):
                self.hass.async_create_task(self.async_room_limits(entity))

        self._cancel_room_listener = self.hass.bus.async_listen("state_changed", changed)

    def _log(self, entity: str, message: str) -> None:
        """Associate explanations with the floor entity's native HA activity."""
        async_log_entry(self.hass, "Gulvkomfort", message, domain=DOMAIN, entity_id=entity)

    async def async_observe(self, entity: str, level: str, observed_at: float | None = None) -> None:
        """Persist first observed transitions, including changes outside the rule.

        An already-active entity has no known physical switch-on timestamp.
        Missing/unavailable states never count as Off or restart an active clock.
        """
        if level not in _OPTIONS:
            return
        async with self.lock:
            if self._closed or self.load_error:
                return
            observations = self.data.setdefault("observations", {})
            previous = observations.get(entity, {})
            if previous.get("level") == level:
                return
            now = observed_at if observed_at is not None else self._now()
            item = {**previous, "level": level}
            if level == "off":
                item.update(active_since=None, time_basis=None, last_off_at=now if previous.get("level") in _OPTIONS[1:] else previous.get("last_off_at"))
                message = "Slukket registreret fra enheden."
            elif previous.get("level") in (None, "off"):
                basis = "observed_transition" if previous.get("level") == "off" else "already_active"
                item.update(active_since=now, time_basis=basis)
                message = "Tændt registreret fra enheden." if basis == "observed_transition" else "Opdaget allerede tændt; det oprindelige tændingstidspunkt er ukendt."
            else:
                message = "Ændret komfortniveau registreret fra enheden; den eksisterende tændingstid bevares."
            observations[entity] = item
            try:
                await self._persist()
            except HomeAssistantError:
                if previous:
                    observations[entity] = previous
                else:
                    observations.pop(entity, None)
                _LOGGER.exception("Could not save observed comfort status for %s", entity)
                return
            if previous or level != "off":
                label = "Fra" if level == "off" else f"Niveau {level[-1]}"
                self._log(entity, f"{message} {label}.")
            async_dispatcher_send(self.hass, SIGNAL_COMFORT_STATUS)

    @callback
    def entity_status(self, entity: str, reported_level: str | None = None) -> dict:
        """Read-only diagnostics; never invent a start time or a stop promise."""
        observed = self.data.get("observations", {}).get(entity, {})
        record = self.data["devices"].get(entity, {})
        owner = self.hass.states.get(record.get("owner", "automation.none"))
        enabled = owner is not None and owner.state == "on"
        scheduled = record.get("next_check_at") if record.get("cycle_mode") == "minimum" else record.get("deadline")
        state = self.hass.states.get(entity)
        level = reported_level if reported_level is not None else state.state if state is not None else None
        running = record.get("phase") == "running" and level == record.get("level")
        return {
            "comfort_observed_on_at": self._time(observed.get("active_since")),
            "comfort_on_time_basis": observed.get("time_basis"),
            "comfort_last_off_at": self._time(observed.get("last_off_at")),
            "comfort_rule": record.get("owner"),
            "comfort_phase": record.get("phase"),
            "comfort_automation_enabled": enabled if record else None,
            "comfort_rule_started_at": self._time(record.get("started_at")),
            "comfort_period_started_at": self._time(record.get("active_at")),
            "comfort_next_check_at": self._time(scheduled) if running and enabled else None,
            "comfort_scheduled_check_at": self._time(scheduled) if running else None,
            "comfort_last_decision": record.get("last_decision"),
            "comfort_last_reason": record.get("last_reason"),
            "comfort_adopted": record.get("adopted", False),
            "comfort_start_evidence": record.get("start_evidence"),
            "comfort_start_temperature_c": record.get("start_trigger_temperature_c"),
        }

    async def async_room_limits(self, climate_entity: str) -> None:
        async with self.lock:
            if self._closed:
                return
            try:
                for entity, record in list(self.data["devices"].items()):
                    config = self.data["rules"][record["owner"]]
                    if record.get("cycle_mode") != "minimum" or not config["use_room_maximum"] or record["phase"] not in ("starting", "running"):
                        continue
                    if self._room_temperature(entity)[1] != climate_entity:
                        continue
                    try:
                        await self._advance(entity, record, config, None, allow_start=False)
                    except HomeAssistantError:
                        _LOGGER.exception("Immediate room-temperature stop needs attention: %s", entity)
            finally:
                self._schedule()

    def _time(self, stamp: float | None) -> str | None:
        return dt_util.as_local(datetime.fromtimestamp(stamp, UTC)).isoformat() if stamp is not None else None

    def _explain(self, entity: str, decision: str, explanation: str, command: str | None = None) -> None:
        """Record decisions in memory only, without changing the control path."""
        record = self.data["devices"].get(entity)
        if record is not None:
            record.update(last_decision=decision, last_reason=explanation)
        if self._evaluation is None:
            return
        rooms = self._evaluation["rooms"]
        if entity in rooms and rooms[entity].get("command") and command is None:
            return  # Keep the command that was actually sent in the first pass.
        if entity in rooms and rooms[entity]["decision"] == "manual_change" and decision == "cooldown":
            return
        if entity in rooms and rooms[entity]["decision"] == "extended" and decision == "extension_running":
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
        if config["cycle_mode"] == "minimum":
            candidates = list(dict.fromkeys(filter(None, (config["outdoor_sensor"], config["source"]))))
            attempts = []
            for entity in candidates:
                source = self.hass.states.get(entity)
                value = None
                if source is not None and source.state not in ("unavailable", "unknown"):
                    weather = entity.startswith("weather.")
                    value = _celsius(source.attributes.get("temperature") if weather else source.state,
                                     source.attributes.get("temperature_unit" if weather else "unit_of_measurement"))
                attempts.append({"source": entity, "valid": value is not None})
                if value is not None:
                    return value, {"status": "valid", "source": entity, "fallback_used": entity != candidates[0], "attempts": attempts,
                                   "explanation": "Aktuel udetemperatur fra føleren; ellers vejrtjenestens temperatur nu. Ingen fremtidig prognose bruges til stop."}
            return None, {"status": "unavailable", "attempts": attempts, "explanation": "Ingen gyldig aktuel udetemperatur; perioden forlænges ved næste stopvurdering."}
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
        if config["cycle_mode"] == "minimum" and config["source_mode"] == "current":
            value, detail = self._current_temperature(config)
            if self._evaluation is not None:
                self._evaluation["temperature_data"] = detail
            return value
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
        label = "Fra" if option == "off" else f"Niveau {option[-1]}"
        self._log(entity, record.get("pending_reason", "Tændbetingelsen er opfyldt." if option != "off" else "Slukbetingelsen er opfyldt.") + f" Anmoder om {label}; afventer bekræftelse fra enheden. Regel: {record['owner']}.")
        try:
            await self.hass.services.async_call("select", "select_option", {"entity_id": entity, "option": option}, blocking=True)
        except Exception as error:
            record["phase"] = "uncertain_start" if option != "off" else "uncertain_stop"
            record["error"] = str(error)
            await self._persist()
            self._log(entity, "Kommandoen kunne ikke bekræftes; ingen automatisk genafsendelse. Kontrollér enhedens status.")
            ir.async_create_issue(self.hass, DOMAIN, f"comfort_rule_{entity}", is_fixable=False, severity=ir.IssueSeverity.ERROR,
                                 translation_key="comfort_command_uncertain", translation_placeholders={"entity": entity})
            raise HomeAssistantError(f"Komfortkommando til {entity} er ikke bekræftet. Ingen automatisk genafsendelse.") from error
        record["confirmed"] = True
        record["settle_until"] = self._now() + 30
        await self._persist()

    async def _cooldown(self, entity: str, record: dict) -> None:
        record.update(phase="cooldown", restart_after=self._now() + record["cooldown_hours"] * 3600, deadline=None)
        if record.get("cycle_mode") == "minimum":
            record["next_check_at"] = None
        await self._persist()
        self._log(entity, f"Regelperioden er afsluttet. Ny automatisk start tidligst {self._time(record['restart_after'])}. Bekræftet niveau: {self._floor(entity)}.")
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
                if record.get("cycle_mode") == "minimum" and record.get("active_at") is None:
                    self._begin_minimum(record, self._now())
                await self._persist()
                self._log(entity, f"Regelperioden er bekræftet aktiv. Næste stopvurdering: {self._time(record.get('next_check_at') or record.get('deadline')) or 'ved næste regelkørsel'}. Regel: {record['owner']}.")
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
            if record.get("cycle_mode") == "minimum":
                await self._advance_minimum(entity, record, config, stop_temperature)
                return
            expired = record.get("deadline") is not None and now >= record["deadline"]
            warm = self._warm_now(config, stop_temperature)
            removed = entity not in config["floor_entities"]
            if expired or warm or removed:
                reason = "Maksimal køretid er udløbet." if expired else "Den aktuelle udetemperatur har nået slukgrænsen." if warm else "Rummet er fjernet fra reglen."
                record["pending_reason"] = reason + (f" Ude nu: {stop_temperature:g} °C; slukgrænse: {config['stop_at']:g} °C." if warm else "")
                self._explain(entity, "stopped", reason + " Gulvkomfort sættes til Fra.", "off")
                record.update(phase="stopping", confirmed=False, settle_until=now + 30)
                await self._command(entity, "off", record)
            else:
                self._explain(entity, "continue", "Komforten fortsætter; ingen slukbetingelse er nået, og ingen ny kommando sendes." if stop_temperature is not None else "Komforten fortsætter uden gyldig aktuel udetemperatur; en gemt maksimal køretid gælder stadig.")
            return
        if record["phase"] == "cooldown" and now >= record["restart_after"] and allow_start and temperature is not None and temperature < config["start_below"] and self._startable(config, current) and (config["cycle_mode"] == "minimum" or not self._warm_now(config, stop_temperature)):
            await self._start(entity, config)
        elif record["phase"] == "cooldown":
            if now < record["restart_after"]:
                prefix = "Rummet blev slukket ved øvre rumgrænse. " if record.get("last_stop_reason") == "room_maximum" else ""
                self._explain(entity, "cooldown", prefix + "Minimumspausen er ikke udløbet; ny start er blokeret.")
            else:
                self._waiting(entity, config, current, temperature, allow_start, stop_temperature)

    def _startable(self, config: dict, current: str | None) -> bool:
        return current == "off" or (config["cycle_mode"] == "minimum" and config["adopt_manual"] and current in _OPTIONS[1:])

    def _begin_minimum(self, record: dict, active_at: float) -> None:
        record["active_at"] = active_at
        record["minimum_until"] = active_at + record["min_runtime_hours"] * 3600
        record["next_check_at"] = record["minimum_until"]

    def _room_temperature(self, entity: str) -> tuple[float | None, str | None]:
        """Use only the thermostat on this floor select's registry device."""
        registry = er.async_get(self.hass)
        floor = registry.async_get(entity)
        if floor is None or floor.device_id is None:
            return None, None
        climates = [entry.entity_id for entry in er.async_entries_for_device(registry, floor.device_id)
                    if entry.domain == "climate" and entry.platform == DOMAIN and not entry.disabled]
        if len(climates) != 1:
            return None, None
        state = self.hass.states.get(climates[0])
        if state is None or state.state in ("unknown", "unavailable"):
            return None, climates[0]
        unit = state.attributes.get("temperature_unit", self.hass.config.units.temperature_unit)
        return _celsius(state.attributes.get("current_temperature"), unit), climates[0]

    async def _advance_minimum(self, entity: str, record: dict, config: dict, stop_temperature: float | None) -> None:
        owner = self.hass.states.get(config["rule_id"])
        if owner is None or owner.state != "on":
            self._explain(entity, "disabled", "Automationen er deaktiveret. Ingen automatisk stopvurdering; gemte tidspunkter nulstilles ikke.")
            return
        room, _ = self._room_temperature(entity)
        if await self._stop_at_room_limit(entity, record, config, room):
            return
        held = record["room_hold"]
        if not config["use_room_minimum"]:
            held = False
        elif room is not None:
            if room < config["room_minimum"]:
                held = True
            elif room >= config["room_minimum"] + config["room_margin"]:
                held = False
        if held != record["room_hold"]:
            record["room_hold"] = held
            await self._persist()
        now = self._now()
        if now < record["next_check_at"]:
            protected = now < record["minimum_until"]
            self._explain(entity, "minimum_runtime" if protected else "extension_running",
                          "Minimumløbetiden beskytter rummet; komforten fortsætter uden nye kommandoer." if protected else "Rummets forlængelsesperiode løber stadig; næste stopvurdering sker ved periodens slutning.")
            return
        removed = entity not in config["floor_entities"]
        room_missing = config["use_room_minimum"] and room is None
        if removed or (stop_temperature is not None and stop_temperature >= config["stop_at"] and not held and not room_missing):
            record["pending_reason"] = "Perioden er udløbet; rummet er fjernet fra reglen." if removed else f"Perioden er udløbet. Ude nu: {stop_temperature:g} °C, slukgrænse: {config['stop_at']:g} °C. Rummet behøver ikke fastholdelse."
            self._explain(entity, "stopped", "Perioden er udløbet, og rummet er fjernet fra reglen." if removed else "Perioden er udløbet, udetemperaturen har nået slukgrænsen, og dette rum behøver ikke fastholdelse.", "off")
            record.update(phase="stopping", confirmed=False, settle_until=now + 30)
            await self._command(entity, "off", record)
            return
        reason = "room_temperature_missing" if room_missing else "room_hold" if held else "outdoor_missing" if stop_temperature is None else "outdoor_cold"
        explanations = {
            "room_temperature_missing": "Rummets egen temperatur kan ikke læses; dette rum får en ny periode uden at gætte.",
            "room_hold": "Dette rum er fastholdt af sin egen minimumstemperatur og får en ny periode. Andre rum vurderes separat.",
            "outdoor_missing": "Ingen gyldig aktuel udetemperatur; dette rum får en ny periode uden at bruge fremtidig prognose som stopgrundlag.",
            "outdoor_cold": "Udetemperaturen er stadig under slukgrænsen; dette rum får en ny periode.",
        }
        record["next_check_at"] = now + record["extension_hours"] * 3600
        record["last_extension_reason"] = reason
        await self._persist()
        self._explain(entity, "extended", explanations[reason])
        self._log(entity, explanations[reason] + f" Ude nu: {stop_temperature if stop_temperature is not None else 'ukendt'} °C; slukgrænse: {config['stop_at']:g} °C. Rum: {room if room is not None else 'ukendt'} °C. Næste stopvurdering: {self._time(record['next_check_at'])}.")

    async def _stop_at_room_limit(self, entity: str, record: dict, config: dict, room: float | None) -> bool:
        if not config["use_room_maximum"] or room is None or room < config["room_maximum"]:
            return False
        record.update(phase="stopping", confirmed=False, settle_until=self._now() + 30,
                      room_hold=False, last_stop_reason="room_maximum")
        record["pending_reason"] = f"Rummet er {room:g} °C og har nået øvre grænse {config['room_maximum']:g} °C. Afbryder den beskyttede periode."
        self._explain(entity, "room_limit_stop", "Rummets øvre temperaturgrænse er nået. Gulvkomfort sættes straks til Fra, også under minimumløbetid eller forlængelse.", "off")
        await self._command(entity, "off", record)
        if self._floor(entity) == "off":
            await self._cooldown(entity, record)
        return True

    def _room_start_blocked(self, entity: str, config: dict, current: str | None) -> bool:
        if config["cycle_mode"] != "minimum" or not config["use_room_maximum"] or current != "off":
            return False
        room, _ = self._room_temperature(entity)
        return room is None or room >= config["room_maximum"]

    def _upgrade_minimum(self, record: dict, config: dict) -> None:
        """Convert an existing run once, without restarting its clock."""
        record.update(cycle_mode="minimum", min_runtime_hours=config["min_runtime_hours"],
                      extension_hours=config["extension_hours"], room_hold=False, adopted=False,
                      minimum_until=None, next_check_at=None, active_at=None, deadline=None)
        if record["phase"] == "running":
            self._begin_minimum(record, record["started_at"])

    def _warm_now(self, config: dict, value: float | None) -> bool:
        return config["use_stop_temperature"] and value is not None and value >= config["stop_at"]

    def _waiting(self, entity: str, config: dict, current: str | None, temperature: float | None, enabled: bool, stop_temperature: float | None = None) -> None:
        if current is None:
            self._explain(entity, "unavailable", "Rummets Gulvkomfort er utilgængelig; ingen kommando sendes.")
        elif not enabled:
            self._explain(entity, "disabled", "Automationen er deaktiveret; ingen ny start tillades.")
        elif current != "off" and not (config["cycle_mode"] == "minimum" and config["adopt_manual"]):
            self._explain(entity, "manual_level", "Komforten er allerede tændt manuelt og overtages ikke af reglen.")
        elif self._room_start_blocked(entity, config, current):
            self._explain(entity, "room_limit_block", "Ny start er blokeret: Rummet er allerede ved øvre temperaturgrænse, eller rumtemperaturen kan ikke læses til grænsekontrollen.")
        elif config["cycle_mode"] != "minimum" and self._warm_now(config, stop_temperature):
            self._explain(entity, "warm_now", "Den aktuelle udetemperatur er ved eller over slukgrænsen; rummet forbliver Fra, selv om prognosen er kold.")
        elif temperature is None:
            self._explain(entity, "missing_temperature", "Der er ingen gyldig temperatur for perioden; rummet tændes ikke.")
        else:
            self._explain(entity, "not_cold_enough", "Temperaturgrundlaget er ikke under tændgrænsen; rummet forbliver Fra.")

    async def _start(self, entity: str, config: dict) -> None:
        now = self._now()
        detail = self._evaluation.get("temperature_data", {}) if self._evaluation else {}
        value = self._evaluation.get("temperature_c") if self._evaluation else None
        outside_now = self._current_temperature(config)[0]
        start_reason = (f"Laveste prognose de næste {config['forecast_hours']:g} timer: {value} °C ved {detail.get('minimum_at', 'ukendt tidspunkt')}; tændgrænse: under {config['start_below']:g} °C. "
                        f"Prognose hentet: {detail.get('fetched_at', 'ukendt')}. Ude nu ved start: {outside_now if outside_now is not None else 'ukendt'} °C. Minimumperiode: {config['min_runtime_hours']:g} timer.") if config['source_mode'] == 'forecast' else f"Temperaturgrundlag: {value} °C; tændgrænse: under {config['start_below']:g} °C."
        if config["cycle_mode"] == "minimum":
            current = self._floor(entity)
            if not self._startable(config, current):
                return
            if self._room_start_blocked(entity, config, current):
                self._waiting(entity, config, current, None, True)
                return
            adopted = current != "off"
            record = {"owner": config["rule_id"], "phase": "running" if adopted else "starting", "level": current if adopted else config["level"],
                      "started_at": now, "deadline": None, "cooldown_hours": config["cooldown_hours"], "restart_after": None,
                      "confirmed": adopted, "settle_until": now + 30}
            self._upgrade_minimum(record, config)
            record["adopted"] = adopted
            record["start_trigger_temperature_c"] = self._evaluation.get("temperature_c") if self._evaluation else None
            record["pending_reason"] = start_reason
            record["start_evidence"] = {"temperature_c": value, "source": config["source"], "forecast_hours": config["forecast_hours"],
                                        "start_below_c": config["start_below"], "minimum_at": detail.get("minimum_at"),
                                        "fetched_at": detail.get("fetched_at"), "source_mode": config["source_mode"],
                                        "outdoor_at_start_c": outside_now, "from_cache": detail.get("from_cache")}
            previous_record = self.data["devices"].get(entity)
            self.data["devices"][entity] = record
            if adopted:
                try:
                    await self._persist()
                except HomeAssistantError:
                    # No physical command was sent, so an uncommitted takeover
                    # can be abandoned without creating an uncertain write.
                    if previous_record is None:
                        self.data["devices"].pop(entity, None)
                    else:
                        self.data["devices"][entity] = previous_record
                    raise
                self._log(entity, start_reason + f" Overtager allerede aktiv komfort uden niveauændring. Minimumperioden starter nu; næste vurdering {self._time(record['next_check_at'])}. Regel: {record['owner']}.")
                if await self._stop_at_room_limit(entity, record, config, self._room_temperature(entity)[0]):
                    return
                self._explain(entity, "adopted", "Den opfyldte startbetingelse overtager dette allerede aktive rum. Det manuelle niveau bevares; minimumløbetiden starter nu uden skrivekommando.")
            else:
                self._explain(entity, "started", "Startbetingelsen er opfyldt. Komforten tændes; minimumløbetiden begynder, når det aktive niveau er bekræftet.", config["level"])
                await self._command(entity, config["level"], record)
            return
        record = {"owner": config["rule_id"], "phase": "starting", "level": config["level"], "started_at": now,
                  "deadline": now + config["max_runtime_hours"] * 3600 if config["use_max_runtime"] else None,
                  "cooldown_hours": config["cooldown_hours"], "restart_after": None, "confirmed": False, "settle_until": now + 30}
        self.data["devices"][entity] = record
        record["pending_reason"] = start_reason
        self._explain(entity, "started", "Temperaturgrundlaget er under tændgrænsen, rummet står på Fra, og ingen pause blokerer. Det valgte komfortniveau aktiveres.", config["level"])
        await self._command(entity, config["level"], record)

    def _needs_start_check(self, entity: str, config: dict) -> bool:
        current = self._floor(entity)
        if not self._startable(config, current) or self._room_start_blocked(entity, config, current):
            return False
        record = self.data["devices"].get(entity)
        if record is None:
            return True
        if record["phase"] != "cooldown" or self._now() < record["restart_after"]:
            return False
        if record["owner"] == config["rule_id"]:
            return True
        previous = self.hass.states.get(record["owner"])
        return previous is None or previous.state != "on"

    async def async_evaluate(self, raw: dict) -> dict:
        config = _config(raw)
        async with self.lock:
            result = {"evaluated_at": self._time(self._now()), "rule_id": config["rule_id"], "source": config["source"],
                      "source_mode": config["source_mode"], "forecast_hours": config["forecast_hours"] if config["source_mode"] == "forecast" else None,
                      "temperature_c": None, "stop_temperature_c": None, "start_below_c": config["start_below"], "stop_at_c": config["stop_at"] if config["cycle_mode"] == "minimum" or config["use_stop_temperature"] else None,
                      "cycle_mode": config["cycle_mode"], "max_runtime_enabled": config["cycle_mode"] != "minimum" and config["use_max_runtime"], "rooms": {}}
            self._evaluation = result
            try:
                if self.load_error:
                    raise HomeAssistantError("Komfortreglernes lager er ugyldigt; styring er blokeret.")
                for entity in config["floor_entities"]:
                    self._floor(entity)
                if self.data["rules"].get(config["rule_id"]) != config:
                    self.data["rules"][config["rule_id"]] = config
                    if config["cycle_mode"] == "minimum":
                        for record in self.data["devices"].values():
                            if record["owner"] == config["rule_id"] and record.get("cycle_mode") != "minimum":
                                self._upgrade_minimum(record, config)
                    await self._persist()
                owner = self.hass.states.get(config["rule_id"])
                enabled = owner is not None and owner.state == "on"
                # Always enforce existing maximum deadlines, even if the source
                # is offline or an upstream forecast request fails.
                for entity, record in list(self.data["devices"].items()):
                    if record["owner"] == config["rule_id"] and record.get("cycle_mode") != "minimum":
                        await self._advance(entity, record, config, None, allow_start=False)
                stop_temperature, stop_data = self._current_temperature(config) if enabled else (None, {"status": "not_evaluated", "explanation": "Automationen er deaktiveret."})
                result["stop_temperature_c"] = stop_temperature
                result["current_temperature_data"] = stop_data
                # A warm-current stop does not depend on a valid forecast or on
                # waiting for the forecast provider to respond.
                if enabled or config["cycle_mode"] == "minimum":
                    for entity, record in list(self.data["devices"].items()):
                        if record["owner"] == config["rule_id"]:
                            await self._advance(entity, record, config, None, allow_start=False, stop_temperature=stop_temperature)
                need_start = enabled and (config["cycle_mode"] != "minimum" or any(self._needs_start_check(entity, config) for entity in config["floor_entities"]))
                temperature = await self._temperature(config) if need_start else None
                result["temperature_c"] = temperature
                result["automation_enabled"] = enabled
                if not enabled:
                    result["temperature_data"] = {"status": "not_evaluated", "explanation": "Automationen er deaktiveret; kun eksisterende slukfrister kontrolleres."}
                elif not need_start:
                    result["temperature_data"] = {"status": "not_needed", "explanation": "Ingen rum er klar til start eller overtagelse. Prognosen bruges ikke til at ændre aktive kørsler."}
                for entity in config["floor_entities"]:
                    record = self.data["devices"].get(entity)
                    if record is not None:
                        if record["owner"] == config["rule_id"]:
                            await self._advance(entity, record, config, temperature, allow_start=enabled, stop_temperature=stop_temperature)
                        elif record["phase"] == "cooldown" and self._now() >= record["restart_after"] and enabled:
                            previous = self.hass.states.get(record["owner"])
                            if (previous is None or previous.state != "on") and temperature is not None and temperature < config["start_below"] and self._startable(config, self._floor(entity)) and (config["cycle_mode"] == "minimum" or not self._warm_now(config, stop_temperature)):
                                await self._start(entity, config)
                        if record["owner"] != config["rule_id"] and entity not in result["rooms"]:
                            self._explain(entity, "other_rule", "Rummet tilhører en anden komfortregel eller dennes pause; denne regel ændrer det ikke.")
                    elif enabled and temperature is not None and temperature < config["start_below"] and self._startable(config, self._floor(entity)) and (config["cycle_mode"] == "minimum" or not self._warm_now(config, stop_temperature)):
                        await self._start(entity, config)
                    else:
                        self._waiting(entity, config, self._floor(entity), temperature, enabled, stop_temperature)
                for entity, item in result["rooms"].items():
                    record = self.data["devices"].get(entity, {})
                    state = self.hass.states.get(entity)
                    item.update(reported_level=state.state if state else None, phase=record.get("phase"),
                                started_at=self._time(record.get("started_at")), maximum_stop_at=self._time(record.get("deadline")),
                                next_start_not_before=self._time(record.get("restart_after")), owner=record.get("owner"))
                    if record.get("cycle_mode") == "minimum":
                        room_value, room_entity = self._room_temperature(entity)
                        item.update(cycle_mode="minimum", adopted=record["adopted"], active_at=self._time(record["active_at"]),
                                    min_runtime_hours=record["min_runtime_hours"], extension_hours=record["extension_hours"],
                                    minimum_until=self._time(record["minimum_until"]), next_check_at=self._time(record["next_check_at"]),
                                    room_temperature_c=room_value, room_temperature_source=room_entity, room_hold=record["room_hold"],
                                    room_minimum_enabled=config["use_room_minimum"], last_extension_reason=record.get("last_extension_reason"),
                                    start_trigger_temperature_c=record.get("start_trigger_temperature_c"))
                        item.update(room_maximum_enabled=config["use_room_maximum"], room_maximum_c=config["room_maximum"] if config["use_room_maximum"] else None,
                                    last_stop_reason=record.get("last_stop_reason"))
                result["explanation"] = "Tændgrundlag: " + (f"{temperature:.2f} °C." if temperature is not None else "ingen gyldig temperatur.")
                if enabled and not need_start:
                    result["explanation"] = "Tændgrundlag ikke vurderet; aktive perioder ændres ikke af nye prognoser."
                result["explanation"] += " Udetemperatur nu (slukgrundlag): " + (f"{stop_temperature:.2f} °C." if stop_temperature is not None else "ingen gyldig aktuel udetemperatur.")
                result["explanation"] += " " + " ".join(f"{entity}: {item['explanation']}" for entity, item in result["rooms"].items())
                return result
            finally:
                self._evaluation = None
                self._schedule()

    @callback
    def _schedule(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_COMFORT_STATUS)
        if self._cancel:
            self._cancel()
            self._cancel = None
        if self._closed:
            return
        deadlines = [r["deadline"] for r in self.data["devices"].values() if r.get("deadline") is not None and r["phase"] != "cooldown"]
        for record in self.data["devices"].values():
            owner = self.hass.states.get(record["owner"])
            if record.get("cycle_mode") != "minimum" or record["phase"] == "cooldown" or owner is None or owner.state != "on":
                continue
            if record["phase"] in ("starting", "uncertain_start", "stopping", "uncertain_stop"):
                deadlines.append(record["settle_until"])
            elif record.get("next_check_at") is not None:
                deadlines.append(record["next_check_at"])
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
                        config = self.data["rules"][record["owner"]]
                        outside = self._current_temperature(config)[0] if record.get("cycle_mode") == "minimum" else None
                        await self._advance(entity, record, config, None, allow_start=False, stop_temperature=outside)
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
        self._closed = True
        if self._cancel_room_listener:
            self._cancel_room_listener()
            self._cancel_room_listener = None
        if self._cancel:
            self._cancel()
            self._cancel = None


async def async_setup_comfort_rules(hass: HomeAssistant) -> None:
    if _KEY in hass.data:
        return
    controller = hass.data[_KEY] = ComfortRules(hass)
    await controller.async_load()
    controller.watch_room_limits()

    async def evaluate(call: ServiceCall) -> dict:
        return await controller.async_evaluate(dict(call.data))

    async def reset(call: ServiceCall) -> None:
        await controller.async_reset(call.data["rule_id"])

    hass.services.async_register(DOMAIN, "evaluate_comfort_rule", evaluate, schema=RULE_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, "reset_comfort_rule", reset, schema=vol.Schema({vol.Required("rule_id"): cv.entity_id}))
    async_at_start(hass, controller.async_deadlines)
    hass.bus.async_listen_once("homeassistant_stop", controller.close)
