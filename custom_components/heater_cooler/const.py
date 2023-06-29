"""Provides the constants needed for component."""

from enum import IntFlag

class CurrentState(IntFlag):
    """Current state enum for heater/cooler devices."""

    INACTIVE = 0
    IDLE = 1
    HEATING = 2
    COOLING = 3

class TargetState(IntFlag):
    """Target state enum for heater/cooler devices."""

    AUTO = 0
    HEAT = 1
    COOL = 2

class Active(IntFlag):
    """Active enum for heater/cooler devices."""

    ACTIVE = 0
    INACTIVE = 1

ATTR_ACTIVE = "active"
ATTR_CURRENT_STATE = "current_state"
ATTR_TARGET_STATE = "target_state"
ATTR_CURRENT_TEMPERATURE = "current_temperature"

DEFAULT_MIN_TEMP = 7
DEFAULT_MAX_TEMP = 35
DEFAULT_MIN_HUMIDITY = 30
DEFAULT_MAX_HUMIDITY = 99

DOMAIN = "heater_cooler"

SERVICE_SET_ACTIVE = "set_active"
SERVICE_SET_TARGET_STATE = "set_target_state"
SERVICE_SET_TEMPERATURE = "set_temperature"

class HeaterCoolerEntityFeature(IntFlag):
    """Supported features of the heater/cooler entity."""

    TARGET_TEMPERATURE = 1
