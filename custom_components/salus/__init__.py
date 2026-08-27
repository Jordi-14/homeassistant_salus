"""Support for Salus iT600."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import Any

from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_validation import config_entry_only_config_schema

from salus_it600.exceptions import (
    IT600AuthenticationError,
    IT600ConnectionError,
    IT600UnsupportedFirmwareError,
)
from salus_it600.gateway import IT600Gateway

from .const import CONNECT_RETRIES, CONNECT_RETRY_DELAY, DOMAIN, GATEWAY_OPERATION_TIMEOUT_SECONDS, PLATFORMS
from .coordinator import SalusConfigEntry, SalusData, SalusDataUpdateCoordinator, SalusRuntimeData
from .sensor import sensor_device_registry_unique_id
from .switch import switch_device_registry_unique_id

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: SalusConfigEntry) -> bool:
    """Set up Salus iT600 from a config entry."""
    gateway = IT600Gateway(
        host=entry.data[CONF_HOST],
        euid=entry.data[CONF_TOKEN],
        session=async_get_clientsession(hass),
    )
    runtime_data: SalusRuntimeData | None = None

    try:
        await _async_connect_gateway(gateway)

        coordinator = SalusDataUpdateCoordinator(hass, entry, gateway)
        runtime_data = SalusRuntimeData(gateway=gateway, coordinator=coordinator)
        entry.runtime_data = runtime_data

        await coordinator.async_config_entry_first_refresh()

        gateway_info = gateway.get_gateway_device()
        coordinator.gateway_id = gateway_info.unique_id
        _async_register_gateway_device(hass, entry, gateway_info)

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    except Exception:
        with suppress(Exception):
            await gateway.close()
        if (
            runtime_data is not None
            and getattr(entry, "runtime_data", None) is runtime_data
        ):
            entry.runtime_data = None
        raise

    return True


async def _async_options_updated(hass: HomeAssistant, entry: SalusConfigEntry) -> None:
    """Reload the config entry when integration options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_connect_gateway(gateway: IT600Gateway) -> None:
    """Connect to the gateway, retrying short-lived connection failures."""
    last_error: Exception | None = None

    for attempt in range(CONNECT_RETRIES):
        try:
            async with asyncio.timeout(GATEWAY_OPERATION_TIMEOUT_SECONDS):
                await gateway.connect()
            return
        except IT600AuthenticationError as ex:
            raise ConfigEntryAuthFailed("Invalid Salus gateway EUID") from ex
        except IT600UnsupportedFirmwareError as ex:
            raise ConfigEntryNotReady(
                "Salus gateway firmware uses an unsupported protocol"
            ) from ex
        except (IT600ConnectionError, TimeoutError) as ex:
            last_error = ex
            if attempt < CONNECT_RETRIES - 1:
                await asyncio.sleep(CONNECT_RETRY_DELAY)

    raise ConfigEntryNotReady("Could not connect to Salus gateway") from last_error


def _async_register_gateway_device(
    hass: HomeAssistant,
    entry: SalusConfigEntry,
    gateway_info: Any,
) -> None:
    """Register the Salus gateway device.

    Creates a Home Assistant device for the gateway itself (parent device for
    all Salus entities). This allows grouping all entities under one device in
    the UI, and provides gateway info (model, firmware version).

    Args:
        hass: Home Assistant instance
        entry: Config entry for this integration instance
        gateway_info: Device info from gateway.get_gateway_device()
    """
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, gateway_info.unique_id)},
        identifiers={(DOMAIN, gateway_info.unique_id)},
        manufacturer=gateway_info.manufacturer,
        name=gateway_info.name,
        model=gateway_info.model,
        sw_version=gateway_info.sw_version,
    )


def _live_device_registry_identifiers(data: SalusData) -> set[str]:
    """Return the device-registry identifier values currently in use.

    Mirrors how entities pick their device identity in device_info: a child
    entity attaches to its parent's device, standalone sensors and grouped
    switch endpoints attach to the physical device's UniID, and every other
    primary entity uses the device snapshot's own unique_id.
    """
    known: set[str] = set()

    for collection_name in (
        "climate_devices",
        "binary_sensor_devices",
        "switch_devices",
        "cover_devices",
        "sensor_devices",
    ):
        for device in getattr(data, collection_name).values():
            parent_unique_id = getattr(device, "parent_unique_id", None)
            if parent_unique_id:
                known.add(parent_unique_id)
                continue

            identifier: str | None = None
            if collection_name == "sensor_devices":
                identifier = sensor_device_registry_unique_id(device)
            elif collection_name == "switch_devices":
                identifier = switch_device_registry_unique_id(device, data)
            if identifier is None:
                identifier = getattr(device, "unique_id", None)
            if identifier is not None:
                known.add(identifier)

    return known


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: SalusConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    """Allow deleting a device from the UI once the gateway stops providing it.

    Without this, Home Assistant answers every delete with "Config entry does
    not support device removal", so registry entries the integration no longer
    provides - devices unpaired from the gateway, or per-entity devices left
    behind by older forks that did not group entities under one physical
    device - stay on the integration page forever.

    Only devices the gateway no longer provides may be removed: the guard
    collects the device-registry identifiers everything currently known
    registers under, and refuses the delete if this device is among them, so a
    live thermostat cannot be deleted by accident. The comparison uses
    device-level identity (parent_unique_id / UniID grouping), not each
    entity's own unique_id: a stale per-entity device must stay deletable even
    while its old identifier lives on as an entity unique_id. Refusing on any
    error is deliberate - if we cannot prove the device is gone, we keep it.
    """
    runtime_data = getattr(config_entry, "runtime_data", None)
    if runtime_data is None:
        return True

    coordinator = runtime_data.coordinator
    try:
        data = coordinator.data
        if data is None:
            _LOGGER.warning(
                "No Salus data snapshot available, refusing removal of device %s",
                device_entry.id,
            )
            return False

        known = _live_device_registry_identifiers(data)
        if coordinator.gateway_id is not None:
            known.add(coordinator.gateway_id)
    except Exception as ex:  # never let a delete crash on an unexpected model
        _LOGGER.warning(
            "Could not determine live Salus devices, refusing removal of device %s: %s",
            device_entry.id,
            ex,
        )
        return False

    return not any(
        identifier in known
        for domain, identifier in device_entry.identifiers
        if domain == DOMAIN
    )


async def async_unload_entry(hass: HomeAssistant, entry: SalusConfigEntry) -> bool:
    """Unload a config entry."""
    runtime_data = entry.runtime_data
    runtime_data.coordinator.async_cancel_debounced_refresh()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        await runtime_data.gateway.close()

    return unload_ok
