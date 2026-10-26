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


class TestThermostatCalibrationSensor:
    """SQ610 temperature calibration offset from the decoded Advanced Settings."""

    def test_reports_offset_as_diagnostic_without_temperature_class(self):
        from salus_it600.models import ThermostatAdvancedSettings

        from custom_components.salus.sensor import SalusThermostatCalibrationSensor
        from tests.conftest import make_climate_device

        device = make_climate_device()
        device.advanced_settings = ThermostatAdvancedSettings(
            temperature_calibration=-0.5
        )
        coord = _coordinator_with_sensors()
        coord.data.climate_devices[device.unique_id] = device
        entity = SalusThermostatCalibrationSensor(coord, device.unique_id)

        assert entity.unique_id == f"{device.unique_id}_temperature_calibration"
        assert entity.device_info["identifiers"] == {(DOMAIN, device.unique_id)}
        assert entity.translation_key == "temperature_calibration"
        assert entity.entity_category == EntityCategory.DIAGNOSTIC
        assert entity.native_unit_of_measurement == "°C"
        assert entity.device_class is None
        assert entity.state_class is None
        assert entity.native_value == -0.5

        device.advanced_settings = None
        assert entity.native_value is None

    async def test_setup_only_adds_thermostats_with_a_decoded_offset(self):
        from types import SimpleNamespace
        from unittest.mock import Mock

        from salus_it600.models import ThermostatAdvancedSettings

        from custom_components.salus.sensor import (
            SalusThermostatCalibrationSensor,
            async_setup_entry,
        )
        from tests.conftest import make_climate_device

        with_offset = make_climate_device("sq610-a")
        with_offset.advanced_settings = ThermostatAdvancedSettings(
            temperature_calibration=1.0
        )
        undecoded = make_climate_device("sq610-b")
        undecoded.advanced_settings = ThermostatAdvancedSettings()
        legacy = make_climate_device("it600-c", model="iT600")

        coord = _coordinator_with_sensors()
        for device in (with_offset, undecoded, legacy):
            coord.data.climate_devices[device.unique_id] = device
        coord.async_add_listener = Mock(return_value=lambda: None)
        entry = SimpleNamespace(
            runtime_data=SimpleNamespace(coordinator=coord), async_on_unload=Mock()
        )
        add_entities = Mock()
        await async_setup_entry(None, entry, add_entities)

        calibration = [
            entity
            for call in add_entities.call_args_list
            for entity in call.args[0]
            if isinstance(entity, SalusThermostatCalibrationSensor)
        ]
        assert [entity.unique_id for entity in calibration] == [
            "sq610-a_temperature_calibration"
        ]


class TestThermostatTemperatureSensor:
    """Verify cached readings, identity, and availability for issue #49."""

    def test_reading_updates_and_groups_with_thermostat(self):
        from custom_components.salus.sensor import SalusThermostatTemperatureSensor
        from tests.conftest import make_climate_device

        device = make_climate_device(current_temperature=19.5)
        coord = _coordinator_with_sensors()
        coord.data.climate_devices[device.unique_id] = device
        entity = SalusThermostatTemperatureSensor(coord, device.unique_id)
        assert entity.unique_id == f"{device.unique_id}_temperature"
        assert entity.device_info["identifiers"] == {(DOMAIN, device.unique_id)}
        assert entity.translation_key == "temperature"
        assert entity.native_unit_of_measurement == "°C"
        assert entity.device_class == SensorDeviceClass.TEMPERATURE
        assert entity.state_class == SensorStateClass.MEASUREMENT
        assert entity.native_value == 19.5
        coord.data.climate_devices[device.unique_id] = make_climate_device(
            current_temperature=0.0
        )
        assert entity.native_value == 0.0
        assert coord.gateway.calls == []
        assert coord.refresh_requests == 0

    def test_missing_reading_and_device_availability(self):
        from custom_components.salus.sensor import SalusThermostatTemperatureSensor
        from tests.conftest import make_climate_device

        device = make_climate_device(current_temperature=None)
        coord = _coordinator_with_sensors()
        coord.data.climate_devices[device.unique_id] = device
        entity = SalusThermostatTemperatureSensor(coord, device.unique_id)
        assert entity.native_value is None
        assert entity.available
        coord.last_update_success = False
        assert not entity.available
        coord.last_update_success = True
        device.available = False
        assert not entity.available
        coord.data.climate_devices.clear()
        assert entity.native_value is None
        assert not entity.available

    async def test_setup_discovers_thermostats_added_after_startup(self):
        from types import SimpleNamespace
        from unittest.mock import Mock

        from custom_components.salus.sensor import (
            SalusThermostatTemperatureSensor,
            async_setup_entry,
        )
        from tests.conftest import make_climate_device

        coord = _coordinator_with_sensors()
        coord.async_add_listener = Mock(return_value=lambda: None)
        entry = SimpleNamespace(
            runtime_data=SimpleNamespace(coordinator=coord), async_on_unload=Mock()
        )
        add_entities = Mock()
        await async_setup_entry(None, entry, add_entities)
        add_entities.assert_not_called()
        device = make_climate_device()
        coord.data.climate_devices[device.unique_id] = device
        for call in coord.async_add_listener.call_args_list:
            call.args[0]()
        add_entities.assert_called_once()
        assert isinstance(
            add_entities.call_args.args[0][0], SalusThermostatTemperatureSensor
        )
        for call in coord.async_add_listener.call_args_list:
            call.args[0]()
        add_entities.assert_called_once()


class TestMiniTrvSensors:
    """it600MINITRV child sensors from the client."""

    def test_trv_temperature_is_a_child_temperature_sensor(self):
        device = make_sensor_device(
            unique_id="trv_001_temperature",
            name="Bedroom TRV Temperature",
            model="it600MINITRV",
            state=20.25,
            device_class="temperature",
            parent_unique_id="trv_001",
            data={"UniID": "trv_001", "Endpoint": 1},
        )
        coord = _coordinator_with_sensors(device)
        entity = SalusSensor(coord, device.unique_id)

        assert entity.native_value == 20.25
        assert entity.translation_key == "temperature"
        assert entity.device_class == SensorDeviceClass.TEMPERATURE
        assert entity.state_class == SensorStateClass.MEASUREMENT
        assert entity.entity_category is None
        assert (DOMAIN, "trv_001") in entity.device_info["identifiers"]

    def test_trv_signal_sensors_are_diagnostic(self):
        rssi = make_sensor_device(
            unique_id="trv_001_rssi",
            name="Bedroom TRV Signal strength",
            model="it600MINITRV",
            state=-58,
            unit_of_measurement="dBm",
            device_class="signal_strength",
            parent_unique_id="trv_001",
            entity_category="diagnostic",
            data={"UniID": "trv_001", "Endpoint": 1},
        )
        coord = _coordinator_with_sensors(rssi)
        entity = SalusSensor(coord, rssi.unique_id)

        assert entity.translation_key == "signal_strength"
        assert entity.entity_category == EntityCategory.DIAGNOSTIC
        assert entity.state_class == SensorStateClass.MEASUREMENT
