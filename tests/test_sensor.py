"""Tests for the Salus sensor entity."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory

from custom_components.salus.const import DOMAIN
from custom_components.salus.coordinator import SalusData
from custom_components.salus.sensor import SalusSensor
from tests.conftest import FakeCoordinator, make_sensor_device


def _coordinator_with_sensors(*devices):
    """Create a FakeCoordinator with sensor devices."""
    data = SalusData(
        climate_devices={},
        binary_sensor_devices={},
        switch_devices={},
        cover_devices={},
        sensor_devices={d.unique_id: d for d in devices},
    )
    return FakeCoordinator(data=data)


class TestSalusSensorProperties:
    """Test sensor entity property delegation."""

    def test_unique_id(self):
        device = make_sensor_device(unique_id="sensor_001_temp")
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, "sensor_001_temp")
        assert entity.unique_id == "sensor_001_temp"

    def test_primary_sensor_name_uses_device_name(self):
        device = make_sensor_device(unique_id="sensor_001_temp")
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, "sensor_001_temp")
        assert entity.name is None
        assert entity.translation_key is None

    def test_native_value(self):
        device = make_sensor_device(state=23.4)
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.native_value == 23.4

    def test_native_unit_temperature(self):
        device = make_sensor_device(unit_of_measurement="°C")
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.native_unit_of_measurement == "°C"

    def test_device_class_temperature(self):
        device = make_sensor_device(device_class="temperature")
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.device_class == SensorDeviceClass.TEMPERATURE

    def test_state_class_measurement(self):
        device = make_sensor_device(device_class="temperature")
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.state_class == SensorStateClass.MEASUREMENT

    def test_state_class_total_increasing_for_energy(self):
        device = make_sensor_device(
            unique_id="switch-1_energy",
            device_class="energy",
            unit_of_measurement="kWh",
            state=12.345,
        )
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.state_class == SensorStateClass.TOTAL_INCREASING

    def test_state_class_measurement_for_power(self):
        device = make_sensor_device(
            unique_id="switch-1_power",
            device_class="power",
            unit_of_measurement="W",
            state=42,
        )
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.state_class == SensorStateClass.MEASUREMENT

    def test_device_info_uses_uni_id(self):
        device = make_sensor_device(
            unique_id="sensor_001_temp",
            data={"UniID": "sensor_001", "Endpoint": 1},
        )
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        info = entity.device_info
        assert (DOMAIN, "sensor_001") in info["identifiers"]

    def test_available_true(self):
        device = make_sensor_device(available=True)
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.available is True

    def test_available_false(self):
        device = make_sensor_device(available=False)
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.available is False


class TestSalusBatterySensor:
    """Test battery sensor (grouped under thermostat device)."""

    def _battery(self):
        return make_sensor_device(
            unique_id="climate_001_battery",
            name="Living Room Battery",
            state=80,
            unit_of_measurement="%",
            device_class="battery",
            parent_unique_id="climate_001",
            entity_category="diagnostic",
            data={"UniID": "climate_001", "Endpoint": 1},
        )

    def test_device_class_battery(self):
        coord = _coordinator_with_sensors(self._battery())
        entity = SalusSensor(coord, "climate_001_battery")
        assert entity.device_class == SensorDeviceClass.BATTERY

    def test_unit_percent(self):
        coord = _coordinator_with_sensors(self._battery())
        entity = SalusSensor(coord, "climate_001_battery")
        assert entity.native_unit_of_measurement == "%"

    def test_native_value(self):
        coord = _coordinator_with_sensors(self._battery())
        entity = SalusSensor(coord, "climate_001_battery")
        assert entity.native_value == 80

    def test_entity_category_diagnostic(self):
        coord = _coordinator_with_sensors(self._battery())
        entity = SalusSensor(coord, "climate_001_battery")
        assert entity.entity_category == EntityCategory.DIAGNOSTIC

    def test_device_info_uses_parent_id(self):
        """Battery sensor groups under parent thermostat device."""
        coord = _coordinator_with_sensors(self._battery())
        entity = SalusSensor(coord, "climate_001_battery")
        info = entity.device_info
        # Parent device grouping via parent_unique_id
        assert (DOMAIN, "climate_001") in info["identifiers"]

    def test_child_entity_translation_key(self):
        coord = _coordinator_with_sensors(self._battery())
        entity = SalusSensor(coord, "climate_001_battery")
        assert entity.translation_key == "battery"


class TestSalusSignalSensors:
    """Signal diagnostics have names, numeric statistics and parent grouping."""

    def test_signal_strength_is_a_translated_measurement(self):
        device = make_sensor_device(
            unique_id="climate_001_rssi",
            name="Living Room Signal strength",
            state=-58,
            unit_of_measurement="dBm",
            device_class="signal_strength",
            parent_unique_id="climate_001",
            entity_category="diagnostic",
        )
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.translation_key == "signal_strength"
        assert entity.native_value == -58
        assert entity.native_unit_of_measurement == "dBm"
        assert entity.state_class == SensorStateClass.MEASUREMENT
        assert entity.entity_category == EntityCategory.DIAGNOSTIC
        assert entity.device_info["identifiers"] == {(DOMAIN, "climate_001")}

    def test_link_quality_is_a_unitless_translated_measurement(self):
        device = make_sensor_device(
            unique_id="climate_001_lqi",
            name="Living Room Link quality",
            state=240,
            unit_of_measurement=None,
            device_class=None,
            parent_unique_id="climate_001",
            entity_category="diagnostic",
        )
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.translation_key == "link_quality"
        assert entity.native_value == 240
        assert entity.native_unit_of_measurement is None
        assert entity.state_class == SensorStateClass.MEASUREMENT
        assert entity.entity_category == EntityCategory.DIAGNOSTIC
        assert entity.device_info["identifiers"] == {(DOMAIN, "climate_001")}


class TestSalusHumiditySensor:
    """Test humidity sensor."""

    def test_device_class_humidity(self):
        device = make_sensor_device(
            unique_id="climate_001_humidity",
            device_class="humidity",
            unit_of_measurement="%",
            state=55,
        )
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.device_class == SensorDeviceClass.HUMIDITY
        assert entity.state_class == SensorStateClass.MEASUREMENT
        assert entity.native_value == 55

    def test_child_entity_translation_key(self):
        device = make_sensor_device(
            unique_id="climate_001_humidity",
            name="Living Room Humidity",
            device_class="humidity",
            unit_of_measurement="%",
            state=55,
            parent_unique_id="climate_001",
        )
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.translation_key == "humidity"

    def test_floor_temperature_translation_key(self):
        device = make_sensor_device(
            unique_id="climate_001_floor_temperature",
            name="Living Room Floor temperature",
            device_class="temperature",
            parent_unique_id="climate_001",
        )
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)
        assert entity.translation_key == "floor_temperature"

    def test_unknown_child_sensor_uses_fallback_name_from_parent_prefix(self):
        parent = make_sensor_device(
            unique_id="standalone_001_temp",
            name="Living Room",
            data={"UniID": "standalone_001", "Endpoint": 1},
        )
        child = make_sensor_device(
            unique_id="standalone_001_unknown_metric",
            name="Living Room Unknown metric",
            device_class=None,
            parent_unique_id="standalone_001",
            data={"UniID": "standalone_001", "Endpoint": 1},
        )
        coord = _coordinator_with_sensors(parent, child)
        entity = SalusSensor(coord, child.unique_id)
        assert entity.translation_key is None
        assert entity.name == "Unknown metric"

    def test_unknown_child_sensor_ignores_sibling_child_as_parent_name(self):
        sibling = make_sensor_device(
            unique_id="standalone_001_humidity",
            name="Living Room Humidity",
            device_class="humidity",
            parent_unique_id="standalone_001",
            data={"UniID": "standalone_001", "Endpoint": 1},
        )
        parent = make_sensor_device(
            unique_id="standalone_001_temp",
            name="Living Room",
            data={"UniID": "standalone_001", "Endpoint": 1},
        )
        child = make_sensor_device(
            unique_id="standalone_001_unknown_metric",
            name="Living Room Unknown metric",
            device_class=None,
            parent_unique_id="standalone_001",
            data={"UniID": "standalone_001", "Endpoint": 1},
        )
        coord = _coordinator_with_sensors(sibling, parent, child)
        entity = SalusSensor(coord, child.unique_id)
        assert entity.translation_key is None
        assert entity.name == "Unknown metric"
