"""Config flow for the Salus iT600 integration."""

from __future__ import annotations

import asyncio
import logging
import string
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN

from salus_it600.exceptions import IT600AuthenticationError, IT600ConnectionError
from salus_it600.gateway import IT600Gateway

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_FLOW_TYPE = "config_flow_device"
CONF_USER = "user"
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


GATEWAY_SETTINGS = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_TOKEN): vol.All(str, _valid_euid),
        vol.Optional(CONF_NAME, default=DEFAULT_GATEWAY_NAME): str,
    }
)


class SalusFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Salus config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Handle a flow initialized by the user to configure a gateway."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            token = user_input[CONF_TOKEN].strip()

            gateway = IT600Gateway(host=host, euid=token)
            try:
                async with asyncio.timeout(10):
                    unique_id = await gateway.connect()
            except IT600ConnectionError:
                errors["base"] = "connect_error"
            except IT600AuthenticationError:
                errors["base"] = "auth_error"
            except TimeoutError:
                errors["base"] = "connect_error"
            except Exception:
                _LOGGER.exception("Unexpected error during Salus config flow")
                errors["base"] = "unknown"
            finally:
                await gateway.close()

            if not errors:
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_FLOW_TYPE: CONF_USER,
                        CONF_HOST: host,
                        CONF_TOKEN: token,
                        "mac": unique_id,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=GATEWAY_SETTINGS,
            errors=errors,
        )
