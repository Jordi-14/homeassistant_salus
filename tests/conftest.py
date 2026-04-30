"""Shared fixtures for Salus integration tests."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from custom_components.salus.coordinator import SalusData


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


# ---------------------------------------------------------------------------
# Fake gateway and coordinator for entity unit tests
# ---------------------------------------------------------------------------


class FakeGateway:
    """Records gateway method calls for assertion."""

    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.command_error: Exception | None = None

    def _record(self, method: str, *args: Any) -> None:
        if self.command_error is not None:
            raise self.command_error
        self.calls.append((method, *args))

    async def turn_on_switch_device(self, device_id: str) -> None:
        self._record("turn_on_switch", device_id)

    async def turn_off_switch_device(self, device_id: str) -> None:
        self._record("turn_off_switch", device_id)

    async def open_cover(self, device_id: str) -> None:
        self._record("open_cover", device_id)

    async def close_cover(self, device_id: str) -> None:
        self._record("close_cover", device_id)

    async def set_cover_position(self, device_id: str, position: int) -> None:
        self._record("set_cover_position", device_id, position)

    async def set_climate_device_locked(self, device_id: str, locked: bool) -> None:
        self._record("set_climate_locked", device_id, locked)

    async def set_climate_device_temperature(
        self, device_id: str, temperature: float
    ) -> None:
        self._record("set_climate_temperature", device_id, temperature)

    async def set_climate_device_mode(self, device_id: str, mode: str) -> None:
        self._record("set_climate_mode", device_id, mode)

    async def set_climate_device_preset(self, device_id: str, preset: str) -> None:
        self._record("set_climate_preset", device_id, preset)

    async def set_climate_device_fan_mode(self, device_id: str, mode: str) -> None:
        self._record("set_climate_fan_mode", device_id, mode)

    async def set_sq610_device_temperature(
        self, device_id: str, setpoint_celsius: float, *, cooling: bool = False
    ) -> None:
        self._record("set_sq610_temperature", device_id, setpoint_celsius, cooling)

    async def set_sq610_device_hvac_mode(self, device_id: str, mode: str) -> None:
        self._record("set_sq610_hvac_mode", device_id, mode)

    async def set_sq610_device_preset(self, device_id: str, preset: str) -> None:
        self._record("set_sq610_preset", device_id, preset)


class FakeCoordinator:
    """Minimal coordinator fake for entity unit tests.

    Provides the interface that SalusEntity and its subclasses expect:
    - .data (SalusData)
    - .gateway (FakeGateway)
    - .gateway_lock (asyncio.Lock)
    - .gateway_id (str)
    - .async_request_debounced_refresh()
    """

    def __init__(self, data: SalusData | None = None) -> None:
        self.gateway = FakeGateway()
        self.gateway_lock = asyncio.Lock()
        self.gateway_id = "gateway-1"
        self.refresh_requests = 0
        self.last_update_success = True
        self.data = data or SalusData(
            climate_devices={},
            binary_sensor_devices={},
            switch_devices={},
            cover_devices={},
            sensor_devices={},
            raw_climate_props={},
        )

    async def async_request_debounced_refresh(self) -> None:
        self.refresh_requests += 1


# ---------------------------------------------------------------------------
# Device fixture factories
# ---------------------------------------------------------------------------


def make_climate_device(
    unique_id: str = "climate-1",
    name: str = "Living Room",
    *,
    model: str = "SQ610RF",
    available: bool = True,
    temperature_unit: str = "°C",
    precision: float = 0.1,
    current_temperature: float = 21.5,
    current_humidity: float | None = 45.0,
    target_temperature: float = 22.0,
    max_temp: float = 35.0,
    min_temp: float = 5.0,
    hvac_mode: str = "heat",
    hvac_action: str = "heating",
    hvac_modes: list[str] | None = None,
    preset_mode: str = "Permanent Hold",
    preset_modes: list[str] | None = None,
    fan_mode: str | None = None,
    fan_modes: list[str] | None = None,
    locked: bool | None = False,
    extra_state_attributes: dict | None = None,
) -> SimpleNamespace:
    """Create a climate device SimpleNamespace."""
    return SimpleNamespace(
        available=available,
        unique_id=unique_id,
        name=name,
        manufacturer="SALUS",
        model=model,
        sw_version=None,
        temperature_unit=temperature_unit,
        precision=precision,
        current_temperature=current_temperature,
        current_humidity=current_humidity,
        target_temperature=target_temperature,
        max_temp=max_temp,
        min_temp=min_temp,
        hvac_mode=hvac_mode,
        hvac_action=hvac_action,
        hvac_modes=hvac_modes or ["heat", "cool"],
        preset_mode=preset_mode,
        preset_modes=preset_modes or ["Follow Schedule", "Permanent Hold", "Off"],
        fan_mode=fan_mode,
        fan_modes=fan_modes,
        locked=locked,
        extra_state_attributes=extra_state_attributes,
    )


def make_fc600_device(unique_id: str = "fc600-1", name: str = "Fan Coil") -> SimpleNamespace:
    """Create an FC600 fan-coil climate device."""
    return make_climate_device(
        unique_id=unique_id,
        name=name,
        model="FC600",
        hvac_mode="heat",
        hvac_modes=["off", "heat", "cool", "auto"],
        preset_mode="Follow Schedule",
        preset_modes=["Follow Schedule", "Permanent Hold", "Temporary Hold", "Eco", "Off"],
        fan_mode="Auto",
        fan_modes=["Auto", "High", "Medium", "Low", "Off"],
        locked=None,
    )


def make_switch_device(
    unique_id: str = "switch-1",
    name: str = "Kitchen Plug",
    *,
    model: str = "SPE600",
    is_on: bool = False,
    device_class: str = "outlet",
    available: bool = True,
) -> SimpleNamespace:
    """Create a switch device SimpleNamespace."""
    return SimpleNamespace(
        available=available,
        unique_id=unique_id,
        name=name,
        manufacturer="SALUS",
        model=model,
        sw_version=None,
        device_class=device_class,
        is_on=is_on,
    )


def make_cover_device(
    unique_id: str = "cover-1",
    name: str = "Bedroom Blinds",
    *,
    model: str = "RS600",
    current_cover_position: int = 75,
    is_opening: bool | None = None,
    is_closing: bool | None = None,
    is_closed: bool = False,
    supported_features: int = 7,  # OPEN | CLOSE | SET_POSITION
    device_class: str | None = None,
    available: bool = True,
) -> SimpleNamespace:
    """Create a cover device SimpleNamespace."""
    return SimpleNamespace(
        available=available,
        unique_id=unique_id,
        name=name,
        manufacturer="SALUS",
        model=model,
        sw_version=None,
        supported_features=supported_features,
        device_class=device_class,
        current_cover_position=current_cover_position,
        is_opening=is_opening,
        is_closing=is_closing,
        is_closed=is_closed,
    )


def make_binary_sensor_device(
    unique_id: str = "binary-1",
    name: str = "Front Door",
    *,
    model: str = "SW600",
    is_on: bool = False,
    device_class: str = "window",
    parent_unique_id: str | None = None,
    entity_category: str | None = None,
    extra_state_attributes: dict | None = None,
    available: bool = True,
) -> SimpleNamespace:
    """Create a binary sensor device SimpleNamespace."""
    return SimpleNamespace(
        available=available,
        unique_id=unique_id,
        name=name,
        manufacturer="SALUS",
        model=model,
        sw_version=None,
        is_on=is_on,
        device_class=device_class,
        parent_unique_id=parent_unique_id,
        entity_category=entity_category,
        extra_state_attributes=extra_state_attributes,
    )


def make_sensor_device(
    unique_id: str = "sensor-1",
    name: str = "Office Temperature",
    *,
    model: str = "TS600",
    state: Any = 23.4,
    unit_of_measurement: str = "°C",
    device_class: str = "temperature",
    parent_unique_id: str | None = None,
    entity_category: str | None = None,
    available: bool = True,
    data: dict | None = None,
) -> SimpleNamespace:
    """Create a sensor device SimpleNamespace."""
    return SimpleNamespace(
        available=available,
        unique_id=unique_id,
        name=name,
        manufacturer="SALUS",
        model=model,
        sw_version=None,
        state=state,
        unit_of_measurement=unit_of_measurement,
        device_class=device_class,
        parent_unique_id=parent_unique_id,
        entity_category=entity_category,
        data=data or {"UniID": unique_id, "Endpoint": 1},
    )

