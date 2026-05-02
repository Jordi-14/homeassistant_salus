"""Config flow for the Salus iT600 integration."""

from __future__ import annotations

import asyncio
import logging
import string
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.helpers import selector

from salus_it600.exceptions import (
    IT600AuthenticationError,
    IT600ConnectionError,
    IT600UnsupportedFirmwareError,
)
from salus_it600.gateway import IT600Gateway

from .const import (
    CONF_POLL_FAILURE_THRESHOLD,
    CONF_POST_COMMAND_REFRESH_DELAY,
    CONF_SCAN_INTERVAL,
    DEFAULT_POLL_FAILURE_THRESHOLD,
    DEFAULT_POST_COMMAND_REFRESH_DELAY,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    MAX_POLL_FAILURE_THRESHOLD,
    MAX_POST_COMMAND_REFRESH_DELAY,
    MAX_SCAN_INTERVAL_SECONDS,
    MIN_POLL_FAILURE_THRESHOLD,
    MIN_POST_COMMAND_REFRESH_DELAY,
    MIN_SCAN_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

CONF_FLOW_TYPE = "config_flow_device"
CONF_USER = "user"
CONF_MAC = "mac"
DEFAULT_GATEWAY_NAME = "Salus iT600 Gateway"


def _valid_euid(value: str) -> str:
    """Validate and normalize a Salus gateway EUID.

    EUID (Extended Unique ID) is the 16-character hexadecimal identifier printed
    on the bottom of the Salus UGE600 gateway. Used for authentication with the
    local gateway API.

    Accepts input in any case and normalizes to uppercase.

    Args:
        value: User-provided EUID string

    Returns:
        Normalized uppercase EUID

    Raises:
        vol.Invalid: If not exactly 16 hex characters
    """
    token = value.strip()
    if len(token) != 16 or any(char not in string.hexdigits for char in token):
        raise vol.Invalid("expected 16 hexadecimal characters")
    return token.upper()


def _required_field(key: str, default: Any | None = None) -> Any:
    """Return a required voluptuous field with an optional default."""
    if default is None:
        return vol.Required(key)
    return vol.Required(key, default=default)


def _optional_field(key: str, default: Any | None = None) -> Any:
    """Return an optional voluptuous field with an optional default."""
    if default is None:
        return vol.Optional(key)
    return vol.Optional(key, default=default)


def _gateway_settings_schema(
    defaults: Mapping[str, Any] | None = None,
    *,
    include_name: bool,
) -> vol.Schema:
    """Return the gateway credential schema for setup and reconfigure flows."""
    defaults = defaults or {}
    schema: dict[Any, Any] = {
        _required_field(CONF_HOST, defaults.get(CONF_HOST)): str,
        _required_field(CONF_TOKEN, defaults.get(CONF_TOKEN)): str,
    }
    if include_name:
        schema[_optional_field(
            CONF_NAME,
            defaults.get(CONF_NAME, DEFAULT_GATEWAY_NAME),
        )] = str
    return vol.Schema(schema)


def _normalized_credentials(user_input: Mapping[str, Any]) -> tuple[str, str]:
    """Return normalized host and EUID values from flow input."""
    return str(user_input[CONF_HOST]).strip(), _valid_euid(str(user_input[CONF_TOKEN]))


async def _async_validate_gateway(host: str, token: str) -> tuple[str | None, str | None]:
    """Validate gateway credentials and return the gateway unique ID or an error key."""
    gateway = IT600Gateway(host=host, euid=token)
    try:
        async with asyncio.timeout(10):
            return await gateway.connect(), None
    except IT600ConnectionError:
        return None, "connect_error"
    except IT600AuthenticationError:
        return None, "auth_error"
    except IT600UnsupportedFirmwareError:
        return None, "unsupported_firmware"
    except TimeoutError:
        return None, "connect_error"
    except Exception:
        _LOGGER.exception("Unexpected error during Salus config flow")
        return None, "unknown"
    finally:
        await gateway.close()


class SalusFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Salus config flow."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SalusOptionsFlowHandler:
        """Create the options flow for this config entry."""
        return SalusOptionsFlowHandler(config_entry)

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Handle a flow initialized by the user to configure a gateway."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                host, token = _normalized_credentials(user_input)
            except vol.Invalid:
                errors[CONF_TOKEN] = "invalid_euid"
            else:
                unique_id, error = await _async_validate_gateway(host, token)
                if error is not None:
                    errors["base"] = error
                elif unique_id is not None:
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input[CONF_NAME],
                        data={
                            CONF_FLOW_TYPE: CONF_USER,
                            CONF_HOST: host,
                            CONF_TOKEN: token,
                            CONF_MAC: unique_id,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=_gateway_settings_schema(include_name=True),
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Allow the user to update gateway connection settings."""
        return await self._async_step_update_existing_entry(
            step_id="reconfigure",
            entry=self._get_reconfigure_entry(),
            user_input=user_input,
        )

    async def async_step_reauth(
        self,
        entry_data: Mapping[str, Any],
    ):
        """Handle a reauthentication request after an EUID failure."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Ask the user for updated gateway credentials."""
        return await self._async_step_update_existing_entry(
            step_id="reauth_confirm",
            entry=self._get_reauth_entry(),
            user_input=user_input,
        )

    async def _async_step_update_existing_entry(
        self,
        *,
        step_id: str,
        entry: config_entries.ConfigEntry,
        user_input: dict[str, Any] | None,
    ):
        """Validate input and update an existing config entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                host, token = _normalized_credentials(user_input)
            except vol.Invalid:
                errors[CONF_TOKEN] = "invalid_euid"
            else:
                unique_id, error = await _async_validate_gateway(host, token)
                if error is not None:
                    errors["base"] = error
                elif unique_id is not None:
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_mismatch(reason="wrong_gateway")
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_HOST: host,
                            CONF_TOKEN: token,
                            CONF_MAC: unique_id,
                        },
                    )

        return self.async_show_form(
            step_id=step_id,
            data_schema=_gateway_settings_schema(
                entry.data,
                include_name=False,
            ),
            errors=errors,
        )


class SalusOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Salus config entry options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self._config_entry = config_entry

    def _options_schema(self) -> vol.Schema:
        """Return the options schema with current values as defaults."""
        current_threshold = self._config_entry.options.get(
            CONF_POLL_FAILURE_THRESHOLD,
            DEFAULT_POLL_FAILURE_THRESHOLD,
        )
        current_scan_interval = self._config_entry.options.get(
            CONF_SCAN_INTERVAL,
            DEFAULT_SCAN_INTERVAL_SECONDS,
        )
        current_post_command_refresh_delay = self._config_entry.options.get(
            CONF_POST_COMMAND_REFRESH_DELAY,
            DEFAULT_POST_COMMAND_REFRESH_DELAY,
        )

        return vol.Schema(
            {
                vol.Optional(
                    CONF_POLL_FAILURE_THRESHOLD,
                    default=current_threshold,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_POLL_FAILURE_THRESHOLD,
                        max=MAX_POLL_FAILURE_THRESHOLD,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current_scan_interval,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL_SECONDS,
                        max=MAX_SCAN_INTERVAL_SECONDS,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
                vol.Optional(
                    CONF_POST_COMMAND_REFRESH_DELAY,
                    default=current_post_command_refresh_delay,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_POST_COMMAND_REFRESH_DELAY,
                        max=MAX_POST_COMMAND_REFRESH_DELAY,
                        step=0.5,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
            }
        )

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage Salus options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_POLL_FAILURE_THRESHOLD: int(
                        user_input[CONF_POLL_FAILURE_THRESHOLD]
                    ),
                    CONF_SCAN_INTERVAL: int(
                        user_input.get(
                            CONF_SCAN_INTERVAL,
                            DEFAULT_SCAN_INTERVAL_SECONDS,
                        )
                    ),
                    CONF_POST_COMMAND_REFRESH_DELAY: float(
                        user_input.get(
                            CONF_POST_COMMAND_REFRESH_DELAY,
                            DEFAULT_POST_COMMAND_REFRESH_DELAY,
                        )
                    ),
                },
            )

        return self.async_show_form(
            step_id="init",
            data_schema=self._options_schema(),
        )
