"""Serve and load the bundled room card without manual dashboard resources."""

from __future__ import annotations

import asyncio
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

CARD_VERSION = "1.4.1"
CARD_PATH = "/salus-dashboard/salus-room-card.js"
CARD_URL = f"{CARD_PATH}?v={CARD_VERSION}"
_LOCK = "salus_room_card_registration_lock"
_REGISTERED = "salus_room_card_registered"
_STATIC_REGISTERED = "salus_room_card_static_registered"


async def async_register_room_card(hass: HomeAssistant) -> None:
    """Register one public static JS file once for all gateway entries.

    The served file has no state or credentials; data and actions still use
    the authenticated Home Assistant frontend connection. Register at domain
    setup so an offline gateway cannot make an existing card type disappear.
    """
    lock = hass.data.setdefault(_LOCK, asyncio.Lock())
    async with lock:
        if hass.data.get(_REGISTERED):
            return
        if not hass.data.get(_STATIC_REGISTERED):
            path = Path(__file__).parent / "frontend" / "salus-room-card.js"
            await hass.http.async_register_static_paths([StaticPathConfig(CARD_PATH, str(path), False)])
            hass.data[_STATIC_REGISTERED] = True
        add_extra_js_url(hass, CARD_URL)
        hass.data[_REGISTERED] = True
