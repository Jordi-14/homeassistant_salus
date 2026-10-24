"""Boot the beta over an epoplavskis-style v1 entry and existing registry IDs."""
from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.salus as salus_init
from custom_components.salus.const import DOMAIN
from tests.conftest import make_climate_device
from tests.test_init import FakeGateway


async def test_legacy_config_and_renamed_climate_entity_survive_beta_setup(hass):
    # Shape taken from epoplavskis/homeassistant_salus config_flow VERSION=1.
    # Synthetic IDs only: no user's gateway, device or configuration is used.
    entry = MockConfigEntry(
        domain=DOMAIN, version=1, unique_id='gateway-1', title='Existing gateway',
        data={'host': '192.0.2.10', 'token': '0000000000000000',
              'mac': 'gateway-1', 'config_flow_device': 'user'},
    )
    entry.add_to_hass(hass)
    devices = dr.async_get(hass)
    old_device = devices.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, 'thermostat-1')},
        manufacturer='SALUS', model='SQ610RFNH', name='Old room',
    )
    entities = er.async_get(hass)
    old_entity = entities.async_get_or_create(
        'climate', DOMAIN, 'thermostat-1', suggested_object_id='existing_hall',
        config_entry=entry, device_id=old_device.id,
    )
    device = make_climate_device(unique_id='thermostat-1', name='Hall', model='SQ610RFNH')
    device.supports_comfort_warm_floor = True
    device.advanced_settings = SimpleNamespace(comfort_warm_floor=1)

    class ExistingGateway(FakeGateway):
        def get_climate_devices(self):
            return {device.unique_id: device}

    with patch.object(salus_init, 'IT600Gateway', ExistingGateway):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get(old_entity.entity_id) is not None
        current = entities.async_get(old_entity.entity_id)
        assert current.unique_id == 'thermostat-1'
        assert current.device_id == old_device.id
        assert entities.async_get_entity_id('climate', DOMAIN, 'thermostat-1') == old_entity.entity_id
        select_id = entities.async_get_entity_id('select', DOMAIN, 'thermostat-1_comfort_warm_floor')
        assert select_id is not None
        assert entities.async_get(select_id).disabled_by is not None
        assert entry.data['host'] == '192.0.2.10'
        assert entry.data['token'] == '0000000000000000'
        assert await hass.config_entries.async_unload(entry.entry_id)
