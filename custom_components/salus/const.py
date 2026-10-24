"""Constants for the Salus iT600 integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "salus"

PLATFORMS: tuple[Platform, ...] = (
    Platform.CLIMATE,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.COVER,
    Platform.SENSOR,
    Platform.LOCK,
    Platform.SELECT,
)

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL_SECONDS = 20
MIN_SCAN_INTERVAL_SECONDS = 10
MAX_SCAN_INTERVAL_SECONDS = 300
DEFAULT_POST_COMMAND_REFRESH_DELAY = 5.0
CONNECT_RETRIES = 3
CONNECT_RETRY_DELAY = 3

# The client gives each gateway request 5 seconds. These caps sit above what
# its normal request sequences can take, so they only stop a stuck operation.
#
# Connect: protocol detection tries up to three encryption variants and then
# probes the gateway, each one a request.
GATEWAY_CONNECT_TIMEOUT_SECONDS = 30
# Poll: readall plus one combined detail request, or up to 8 per-family detail
# requests on gateways that need them. Waiting for a running command to release
# the gateway is not counted.
GATEWAY_POLL_TIMEOUT_SECONDS = 60

# Timeout for one user command. Some commands send two writes (mode, then the
# preset to restore), and the client retries a write once after a disconnect.
GATEWAY_COMMAND_TIMEOUT_SECONDS = 15

# Debounce windows that collapse rapid slider/setpoint changes into one write.
TARGET_TEMPERATURE_DEBOUNCE_SECONDS = 0.3
COVER_POSITION_DEBOUNCE_SECONDS = 0.3

CONF_POLL_FAILURE_THRESHOLD = "poll_failure_threshold"
DEFAULT_POLL_FAILURE_THRESHOLD = 3
MIN_POLL_FAILURE_THRESHOLD = 0
MAX_POLL_FAILURE_THRESHOLD = 50

CONF_POST_COMMAND_REFRESH_DELAY = "post_command_refresh_delay"
MIN_POST_COMMAND_REFRESH_DELAY = 0.0
MAX_POST_COMMAND_REFRESH_DELAY = 30.0
