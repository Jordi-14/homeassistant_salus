"""Support for Salus iT600."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from salus_it600.exceptions import (
    IT600AuthenticationError,
    IT600ConnectionError,
    IT600UnsupportedFirmwareError,
)
from salus_it600.gateway import IT600Gateway

from .const import CONNECT_RETRIES, CONNECT_RETRY_DELAY, DOMAIN, PLATFORMS
from .coordinator import SalusDataUpdateCoordinator, SalusRuntimeData


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Salus iT600 from a config entry."""
    gateway = IT600Gateway(host=entry.data[CONF_HOST], euid=entry.data[CONF_TOKEN])
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

        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime_data
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        with suppress(Exception):
            await gateway.close()
        if (
            runtime_data is not None
            and getattr(entry, "runtime_data", None) is runtime_data
        ):
            entry.runtime_data = None
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        raise

    return True


async def _async_connect_gateway(gateway: IT600Gateway) -> None:
    """Connect to the gateway, retrying short-lived connection failures."""
    last_error: Exception | None = None

    for attempt in range(CONNECT_RETRIES):
        try:
            async with asyncio.timeout(10):
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
    entry: ConfigEntry,
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


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    runtime_data: SalusRuntimeData = entry.runtime_data
    runtime_data.coordinator.async_cancel_debounced_refresh()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        await runtime_data.gateway.close()
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    return unload_ok
