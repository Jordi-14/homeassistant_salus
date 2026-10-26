"""Tests for the Salus binary sensor entity."""

from __future__ import annotations

from homeassistant.const import EntityCategory

from custom_components.salus.binary_sensor import SalusBinarySensor
from custom_components.salus.const import DOMAIN
from custom_components.salus.coordinator import SalusData
from tests.conftest import FakeCoordinator, make_binary_sensor_device


def _coordinator_with_binary_sensors(*devices):
    """Create a FakeCoordinator with binary sensor devices."""
    data = SalusData(
        climate_devices={},
        binary_sensor_devices={d.unique_id: d for d in devices},
        switch_devices={},
        cover_devices={},
        sensor_devices={},
    )
    return FakeCoordinator(data=data)


class TestSalusBinarySensorProperties:
    """Test binary sensor entity property delegation."""

    def test_unique_id(self):
        device = make_binary_sensor_device(unique_id="binary_001")
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, "binary_001")
        assert entity.unique_id == "binary_001"

    def test_primary_binary_sensor_name_uses_device_name(self):
        device = make_binary_sensor_device(unique_id="binary_001")
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, "binary_001")
        assert entity.name is None
        assert entity.translation_key is None

    def test_is_on_false(self):
        device = make_binary_sensor_device(is_on=False)
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.is_on is False

    def test_is_on_true(self):
        device = make_binary_sensor_device(is_on=True)
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.is_on is True

    def test_device_class_window(self):
        device = make_binary_sensor_device(device_class="window")
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.device_class == "window"

    def test_device_class_moisture(self):
        device = make_binary_sensor_device(
            unique_id="wls-1", device_class="moisture", model="WLS600"
        )
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.device_class == "moisture"

    def test_device_class_smoke(self):
        device = make_binary_sensor_device(
            unique_id="smoke-1", device_class="smoke", model="SmokeSensor-EM"
        )
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.device_class == "smoke"

    def test_device_info(self):
        device = make_binary_sensor_device(unique_id="binary_001", model="SW600")
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, "binary_001")
        info = entity.device_info
        assert info["manufacturer"] == "SALUS"
        assert info["model"] == "SW600"
        assert (DOMAIN, "binary_001") in info["identifiers"]

    def test_available_true(self):
        device = make_binary_sensor_device(available=True)
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.available is True

    def test_available_false(self):
        device = make_binary_sensor_device(available=False)
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.available is False


class TestSalusBinarySensorParentDevice:
    """Test binary sensor with parent_unique_id (error sensors on thermostats)."""

    def _error_device(self):
        return make_binary_sensor_device(
            unique_id="climate_001_problem",
            name="Living Room Problem",
            model="iT600",
            is_on=True,
            device_class="problem",
            parent_unique_id="climate_001",
            entity_category="diagnostic",
            extra_state_attributes={"errors": ["Paired TRV hardware issue"]},
        )

    def test_device_info_uses_parent_id(self):
        device = self._error_device()
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        info = entity.device_info
        assert (DOMAIN, "climate_001") in info["identifiers"]
        # Should only provide identifiers, not override parent device name
        assert "name" not in info

    def test_device_class_problem(self):
        device = self._error_device()
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.device_class == "problem"

    def test_is_on(self):
        device = self._error_device()
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.is_on is True

    def test_entity_category_diagnostic(self):
        device = self._error_device()
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.entity_category == EntityCategory.DIAGNOSTIC

    def test_extra_state_attributes(self):
        device = self._error_device()
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.extra_state_attributes == {
            "errors": ["Paired TRV hardware issue"]
        }

    def test_child_entity_translation_key(self):
        device = self._error_device()
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.translation_key == "problem"


class TestLowBatterySensor:
    """Test low_battery binary sensor (TRV)."""

    def test_battery_problem_sensor(self):
        device = make_binary_sensor_device(
            unique_id="trv_001_battery_problem",
            name="TRV Battery",
            model="it600MINITRV",
            is_on=False,
            device_class="battery",
            parent_unique_id="trv_001",
            entity_category="diagnostic",
        )
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.device_class == "battery"
        assert entity.is_on is False
        assert entity.entity_category == EntityCategory.DIAGNOSTIC
        assert entity.translation_key == "battery_problem"

    def test_low_battery_sensor_translation_key(self):
        device = make_binary_sensor_device(
            unique_id="window_001_low_battery",
            name="Window Low battery",
            model="SW600",
            is_on=False,
            device_class="battery",
            parent_unique_id="window_001",
            entity_category="diagnostic",
        )
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.translation_key == "low_battery"

    def test_open_window_sensor_translation_key(self):
        device = make_binary_sensor_device(
            unique_id="climate_001_open_window",
            name="Living Room Open window",
            model="SQ610RF",
            is_on=True,
            device_class="window",
            parent_unique_id="climate_001",
        )
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)
        assert entity.translation_key == "open_window"


class TestMiniTrvBinarySensors:
    """it600MINITRV heat and problem binary sensors from the client."""

    def test_heat_sensor_exposes_paired_thermostat(self):
        attributes = {
            "paired_thermostat_short_id": 23917,
            "paired_thermostat_id": "climate_001",
            "paired_thermostat_name": "Bedroom Thermostat",
        }
        device = make_binary_sensor_device(
            unique_id="trv_001",
            name="Bedroom TRV",
            model="it600MINITRV",
            is_on=True,
            device_class="heat",
            extra_state_attributes=attributes,
        )
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)

        assert entity.is_on is True
        assert entity.device_class == "heat"
        assert entity.extra_state_attributes == attributes

    def test_problem_sensor_lists_faults(self):
        device = make_binary_sensor_device(
            unique_id="trv_001_problem",
            name="Bedroom TRV Problem",
            model="it600MINITRV",
            is_on=True,
            device_class="problem",
            parent_unique_id="trv_001",
            entity_category="diagnostic",
            extra_state_attributes={"errors": ["Gear issue"]},
        )
        coord = _coordinator_with_binary_sensors(device)
        entity = SalusBinarySensor(coord, device.unique_id)

        assert entity.translation_key == "problem"
        assert entity.entity_category == EntityCategory.DIAGNOSTIC
        assert entity.extra_state_attributes == {"errors": ["Gear issue"]}
        assert (DOMAIN, "trv_001") in entity.device_info["identifiers"]
