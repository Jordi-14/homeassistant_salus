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
    Platform.LOCK,
)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=20)
DEFAULT_FAST_REFRESH_DELAY = 0.5
DEFAULT_POST_COMMAND_REFRESH_DELAY = 3.0
CONNECT_RETRIES = 3
CONNECT_RETRY_DELAY = 3

CONF_POLL_FAILURE_THRESHOLD = "poll_failure_threshold"
DEFAULT_POLL_FAILURE_THRESHOLD = 3
MIN_POLL_FAILURE_THRESHOLD = 0
MAX_POLL_FAILURE_THRESHOLD = 50

CONF_POST_COMMAND_REFRESH_DELAY = "post_command_refresh_delay"
MIN_POST_COMMAND_REFRESH_DELAY = 0.0
MAX_POST_COMMAND_REFRESH_DELAY = 30.0
