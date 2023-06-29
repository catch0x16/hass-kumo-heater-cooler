"""Constants for the Kumo integration."""

from datetime import timedelta
from typing import Final

from ..heater_cooler.const import (
    DOMAIN as HEATER_COOLER_DOMAIN
)

DEFAULT_NAME = "Kumo"
DOMAIN = "kumo"
KUMO_DATA = "data"
KUMO_DATA_COORDINATORS = "coordinators"
KUMO_CONFIG_CACHE = "kumo_cache.json"
CONF_PREFER_CACHE = "prefer_cache"
CONF_ENABLE_POWER_SWITCH = "enable_power_switch"
CONF_CONNECT_TIMEOUT = "connect_timeout"
CONF_RESPONSE_TIMEOUT = "response_timeout"
MAX_AVAILABILITY_TRIES = 3 # How many times we will attempt to update from a kumo before marking it unavailable

PLATFORMS: Final = [HEATER_COOLER_DOMAIN]

# This is the new way of important platforms, but isn't public yet
# from homeassistant.const import Platform
# PLATFORMS: Final = [Platform.CLIMATE, Platform.SENSOR, Platform.SWITCH]

SCAN_INTERVAL = timedelta(seconds=60)
