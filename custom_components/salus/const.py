"""Constants for the Salus iT600 integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "salus"

PLATFORMS: tuple[Platform, ...] = (
    Platform.CLIMATE,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.COVER,
    Platform.SENSOR,
)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)
CONNECT_RETRIES = 3
CONNECT_RETRY_DELAY = 3
