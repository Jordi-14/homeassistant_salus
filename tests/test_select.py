"""Tests for the Salus it600MINITRV mode select entity."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from homeassistant.exceptions import HomeAssistantError
from salus_it600.const import MiniTrvMode
from salus_it600.exceptions import IT600ConnectionError

from custom_components.salus.const import DOMAIN
from custom_components.salus.coordinator import SalusData
from custom_components.salus.select import SalusMiniTrvModeSelect, async_setup_entry
from tests.conftest import FakeCoordinator, make_binary_sensor_device


def _make_trv(unique_id: str = "trv-1", mode: int | None = 0, **kwargs):
    """Create an it600MINITRV heat sensor carrying a reported mode."""
    return make_binary_sensor_device(
        unique_id,
        "Bedroom TRV",
        model="it600MINITRV",
        device_class="heat",
        mini_trv_mode=mode,
        **kwargs,
    )


def _coordinator_with(*devices):
    """Create a FakeCoordinator holding the given binary sensor devices."""
    data = SalusData(
        climate_devices={},
        binary_sensor_devices={device.unique_id: device for device in devices},
        switch_devices={},
        cover_devices={},
        sensor_devices={},
    )
    return FakeCoordinator(data=data)


class TestSalusMiniTrvModeSelectSetup:
    """Test which devices get a mode select."""

    async def test_only_mini_trvs_reporting_a_mode_get_a_select(self):
        trv = _make_trv("trv-1")
        no_mode = _make_trv("trv-2", mode=None)
        low_battery = _make_trv(
            "trv-1_low_battery", mode=None, parent_unique_id="trv-1"
        )
        receiver = make_binary_sensor_device(
            "rx-1", model="it600Receiver", device_class="running", mini_trv_mode=1
        )
        coord = _coordinator_with(trv, no_mode, low_battery, receiver)
        coord.async_add_listener = Mock(return_value=lambda: None)
        entry = SimpleNamespace(
            runtime_data=SimpleNamespace(coordinator=coord), async_on_unload=Mock()
        )
        add_entities = Mock()

        await async_setup_entry(None, entry, add_entities)

        selects = [
            entity
            for call in add_entities.call_args_list
            for entity in call.args[0]
            if isinstance(entity, SalusMiniTrvModeSelect)
        ]
        assert [entity.unique_id for entity in selects] == ["trv-1_mode"]


class TestSalusMiniTrvModeSelectProperties:
    """Test select entity property delegation."""

    def test_identity_and_options(self):
        coord = _coordinator_with(_make_trv())
        entity = SalusMiniTrvModeSelect(coord, "trv-1")
        assert entity.unique_id == "trv-1_mode"
        assert entity.translation_key == "trv_mode"
        assert entity.options == ["auto", "manual_on", "manual_off"]
        assert (DOMAIN, "trv-1") in entity.device_info["identifiers"]

    @pytest.mark.parametrize(
        ("mode", "option"),
        [(0, "auto"), (1, "manual_on"), (2, "manual_off"), (4, None)],
    )
    def test_current_option_follows_reported_mode(self, mode, option):
        coord = _coordinator_with(_make_trv(mode=mode))
        entity = SalusMiniTrvModeSelect(coord, "trv-1")
        assert entity.current_option == option


class TestSalusMiniTrvModeSelectCommands:
    """Test mode changes forwarded to the gateway."""

    @pytest.mark.parametrize(
        ("option", "mode"),
        [
            ("auto", MiniTrvMode.AUTO),
            ("manual_on", MiniTrvMode.MANUAL_ON),
            ("manual_off", MiniTrvMode.MANUAL_OFF),
        ],
    )
    async def test_select_option_sets_mode(self, option, mode):
        coord = _coordinator_with(_make_trv(mode=2 if option == "auto" else 0))
        entity = SalusMiniTrvModeSelect(coord, "trv-1")
        await entity.async_select_option(option)
        assert ("set_mini_trv_mode", "trv-1", mode) in coord.gateway.calls
        assert coord.refresh_requests == 1

    async def test_selection_is_pending_until_confirmation(self):
        device = _make_trv(mode=0)
        coord = _coordinator_with(device)
        entity = SalusMiniTrvModeSelect(coord, "trv-1")

        await entity.async_select_option("manual_on")

        assert entity.current_option == "manual_on"

        device.mini_trv_mode = 1
        assert entity.current_option == "manual_on"

        device.mini_trv_mode = 0
        assert entity.current_option == "auto"

    async def test_gateway_error_raises(self):
        coord = _coordinator_with(_make_trv())
        coord.gateway.command_error = IT600ConnectionError("offline")
        entity = SalusMiniTrvModeSelect(coord, "trv-1")
        with pytest.raises(HomeAssistantError, match="Failed to"):
            await entity.async_select_option("manual_off")
        assert entity.current_option == "auto"
