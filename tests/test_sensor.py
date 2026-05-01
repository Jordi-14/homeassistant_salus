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
        raw_climate_props={},
    )
    return FakeCoordinator(data=data)


class TestSalusSensorProperties:
    """Test sensor entity property delegation."""

    def test_unique_id(self):
        device = make_sensor_device(unique_id="sensor_001_temp")
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, "sensor_001_temp")
        assert entity.unique_id == "sensor_001_temp"

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
