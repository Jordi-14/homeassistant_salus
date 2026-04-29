"""Small Home Assistant compatibility shim for local unit tests.

The real Home Assistant test harness is intentionally not required for these
fast unit tests. This shim only implements the imports and methods exercised by
the local tests.
"""

from __future__ import annotations

import sys
import types
from enum import IntFlag, StrEnum
from pathlib import Path
from types import SimpleNamespace
from typing import Any

CLIENT_ROOT = Path(__file__).resolve().parents[2] / "salus-it600-client"
if str(CLIENT_ROOT) not in sys.path:
    sys.path.insert(0, str(CLIENT_ROOT))


class ConfigEntryAuthFailed(Exception):
    """Test stand-in for Home Assistant's ConfigEntryAuthFailed."""


class ConfigEntryNotReady(Exception):
    """Test stand-in for Home Assistant's ConfigEntryNotReady."""


class UpdateFailed(Exception):
    """Test stand-in for Home Assistant's UpdateFailed."""


ISSUES: dict[tuple[str, str], dict[str, Any]] = {}


class AbortFlow(Exception):
    """Raised by the config-flow shim when a unique ID already exists."""


class DataUpdateCoordinator:
    """Minimal DataUpdateCoordinator stand-in for coordinator unit tests."""

    def __class_getitem__(cls, _item: Any) -> type[DataUpdateCoordinator]:
        return cls

    def __init__(self, *args: Any, **_kwargs: Any) -> None:
        self.hass = args[0] if args else None
        self.data = None
        self.refresh_count = 0

    async def async_request_refresh(self) -> None:
        self.refresh_count += 1

    async def async_config_entry_first_refresh(self) -> None:
        self.data = await self._async_update_data()

    def async_add_listener(self, _listener: Any) -> Any:
        return lambda: None


class CoordinatorEntity:
    """Minimal CoordinatorEntity stand-in."""

    def __class_getitem__(cls, _item: Any) -> type[CoordinatorEntity]:
        return cls

    def __init__(self, coordinator: Any) -> None:
        self.coordinator = coordinator

    @property
    def available(self) -> bool:
        return True


class ConfigFlow:
    """Minimal ConfigFlow stand-in."""

    VERSION = 1

    def __init_subclass__(cls, **_kwargs: Any) -> None:
        super().__init_subclass__()

    def __init__(self) -> None:
        self.unique_id: str | None = None
        self.reconfigure_entry: Any | None = None
        self.reauth_entry: Any | None = None

    async def async_set_unique_id(self, unique_id: str) -> None:
        self.unique_id = unique_id

    def _abort_if_unique_id_configured(self) -> None:
        return None

    def _abort_if_unique_id_mismatch(self, **_kwargs: Any) -> None:
        return None

    def _get_reconfigure_entry(self) -> Any:
        return self.reconfigure_entry

    def _get_reauth_entry(self) -> Any:
        return self.reauth_entry

    def async_update_reload_and_abort(self, entry: Any, **kwargs: Any) -> dict[str, Any]:
        data_updates = kwargs.get("data_updates", {})
        entry.data = {**entry.data, **data_updates}
        return {"type": "abort", "reason": "reconfigure_successful"}

    def async_create_entry(self, **kwargs: Any) -> dict[str, Any]:
        return {"type": "create_entry", **kwargs}

    def async_show_form(self, **kwargs: Any) -> dict[str, Any]:
        return {"type": "form", **kwargs}


class OptionsFlow:
    """Minimal OptionsFlow stand-in."""

    def async_create_entry(self, **kwargs: Any) -> dict[str, Any]:
        return {"type": "create_entry", **kwargs}

    def async_show_form(self, **kwargs: Any) -> dict[str, Any]:
        return {"type": "form", **kwargs}


class Platform:
    """Minimal Home Assistant Platform enum stand-in."""

    CLIMATE = "climate"
    BINARY_SENSOR = "binary_sensor"
    SWITCH = "switch"
    COVER = "cover"
    SENSOR = "sensor"
    LOCK = "lock"


class EntityCategory(StrEnum):
    """Minimal EntityCategory stand-in."""

    CONFIG = "config"
    DIAGNOSTIC = "diagnostic"


class IssueSeverity(StrEnum):
    """Minimal repairs issue severity stand-in."""

    ERROR = "error"
    WARNING = "warning"


class HVACMode(StrEnum):
    """Minimal HVACMode stand-in."""

    OFF = "off"
    HEAT = "heat"
    COOL = "cool"
    AUTO = "auto"


class HVACAction(StrEnum):
    """Minimal HVACAction stand-in."""

    OFF = "off"
    HEATING = "heating"
    COOLING = "cooling"
    IDLE = "idle"


class ClimateEntityFeature(IntFlag):
    """Minimal ClimateEntityFeature stand-in."""

    TARGET_TEMPERATURE = 1
    FAN_MODE = 8
    PRESET_MODE = 16
    TURN_OFF = 128
    TURN_ON = 256


class VolInvalid(Exception):
    """Minimal voluptuous Invalid stand-in."""


class VolSchema:
    """Minimal voluptuous Schema stand-in."""

    def __init__(self, schema: Any) -> None:
        self.schema = schema


def _vol_key(key: Any, **_kwargs: Any) -> Any:
    return key


def _vol_all(*validators: Any) -> Any:
    def _validate(value: Any) -> Any:
        for validator in validators:
            value = validator(value)
        return value

    return _validate


def _vol_range(**kwargs: Any) -> Any:
    minimum = kwargs.get("min")
    maximum = kwargs.get("max")

    def _validate(value: Any) -> Any:
        if minimum is not None and value < minimum:
            raise VolInvalid("value is below minimum")
        if maximum is not None and value > maximum:
            raise VolInvalid("value is above maximum")
        return value

    return _validate


def _callback(func: Any) -> Any:
    return func


def _async_redact_data(data: Any, to_redact: set[str]) -> Any:
    """Minimal diagnostics redaction helper."""
    if isinstance(data, dict):
        return {
            key: "**REDACTED**"
            if key in to_redact
            else _async_redact_data(value, to_redact)
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [_async_redact_data(value, to_redact) for value in data]
    return data


def _async_create_issue(
    _hass: Any,
    domain: str,
    issue_id: str,
    **kwargs: Any,
) -> None:
    """Store a repairs issue in the local test registry."""
    ISSUES[(domain, issue_id)] = kwargs


def _async_delete_issue(_hass: Any, domain: str, issue_id: str) -> None:
    """Delete a repairs issue from the local test registry."""
    ISSUES.pop((domain, issue_id), None)


def install() -> None:
    """Install the shim modules into sys.modules."""
    homeassistant = types.ModuleType("homeassistant")
    components = types.ModuleType("homeassistant.components")
    binary_sensor = types.ModuleType("homeassistant.components.binary_sensor")
    climate = types.ModuleType("homeassistant.components.climate")
    climate_const = types.ModuleType("homeassistant.components.climate.const")
    diagnostics = types.ModuleType("homeassistant.components.diagnostics")
    cover = types.ModuleType("homeassistant.components.cover")
    lock = types.ModuleType("homeassistant.components.lock")
    sensor = types.ModuleType("homeassistant.components.sensor")
    switch = types.ModuleType("homeassistant.components.switch")
    config_entries = types.ModuleType("homeassistant.config_entries")
    core = types.ModuleType("homeassistant.core")
    const = types.ModuleType("homeassistant.const")
    exceptions = types.ModuleType("homeassistant.exceptions")
    helpers = types.ModuleType("homeassistant.helpers")
    device_registry = types.ModuleType("homeassistant.helpers.device_registry")
    entity = types.ModuleType("homeassistant.helpers.entity")
    issue_registry = types.ModuleType("homeassistant.helpers.issue_registry")
    update_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")
    voluptuous = types.ModuleType("voluptuous")

    binary_sensor.BinarySensorEntity = type("BinarySensorEntity", (), {})
    climate.ClimateEntity = type("ClimateEntity", (), {})
    climate_const.FAN_AUTO = "auto"
    climate_const.FAN_HIGH = "high"
    climate_const.FAN_LOW = "low"
    climate_const.FAN_MEDIUM = "medium"
    climate_const.FAN_OFF = "off"
    climate_const.ClimateEntityFeature = ClimateEntityFeature
    climate_const.HVACAction = HVACAction
    climate_const.HVACMode = HVACMode
    diagnostics.async_redact_data = _async_redact_data
    cover.ATTR_POSITION = "position"
    cover.CoverEntity = type("CoverEntity", (), {})
    lock.LockEntity = type("LockEntity", (), {})
    sensor.SensorEntity = type("SensorEntity", (), {})
    switch.SwitchEntity = type("SwitchEntity", (), {})

    config_entries.ConfigEntry = type("ConfigEntry", (), {})
    config_entries.ConfigFlow = ConfigFlow
    config_entries.OptionsFlow = OptionsFlow
    core.HomeAssistant = type("HomeAssistant", (), {})
    core.callback = _callback
    const.ATTR_TEMPERATURE = "temperature"
    const.CONF_HOST = "host"
    const.CONF_NAME = "name"
    const.CONF_TOKEN = "token"
    const.EntityCategory = EntityCategory
    const.Platform = Platform
    exceptions.ConfigEntryAuthFailed = ConfigEntryAuthFailed
    exceptions.ConfigEntryNotReady = ConfigEntryNotReady
    device_registry.CONNECTION_NETWORK_MAC = "mac"
    device_registry.async_get = lambda _hass: SimpleNamespace(
        async_get_or_create=lambda **_kwargs: None
    )
    entity.DeviceInfo = dict
    issue_registry.IssueSeverity = IssueSeverity
    issue_registry.async_create_issue = _async_create_issue
    issue_registry.async_delete_issue = _async_delete_issue
    update_coordinator.CoordinatorEntity = CoordinatorEntity
    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    update_coordinator.UpdateFailed = UpdateFailed

    voluptuous.All = _vol_all
    voluptuous.Invalid = VolInvalid
    voluptuous.Optional = _vol_key
    voluptuous.Range = _vol_range
    voluptuous.Required = _vol_key
    voluptuous.Schema = VolSchema

    homeassistant.components = components
    homeassistant.config_entries = config_entries
    homeassistant.const = const
    homeassistant.core = core
    homeassistant.exceptions = exceptions
    homeassistant.helpers = helpers
    helpers.device_registry = device_registry
    helpers.entity = entity
    helpers.issue_registry = issue_registry
    helpers.update_coordinator = update_coordinator

    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.binary_sensor"] = binary_sensor
    sys.modules["homeassistant.components.climate"] = climate
    sys.modules["homeassistant.components.climate.const"] = climate_const
    sys.modules["homeassistant.components.diagnostics"] = diagnostics
    sys.modules["homeassistant.components.cover"] = cover
    sys.modules["homeassistant.components.lock"] = lock
    sys.modules["homeassistant.components.sensor"] = sensor
    sys.modules["homeassistant.components.switch"] = switch
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.const"] = const
    sys.modules["homeassistant.exceptions"] = exceptions
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.device_registry"] = device_registry
    sys.modules["homeassistant.helpers.entity"] = entity
    sys.modules["homeassistant.helpers.issue_registry"] = issue_registry
    sys.modules["homeassistant.helpers.update_coordinator"] = update_coordinator
    sys.modules["voluptuous"] = voluptuous
