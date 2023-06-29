"""HomeAssistant climate component for KumoCloud connected HVAC units."""
import logging

import voluptuous as vol
from homeassistant.components.climate import PLATFORM_SCHEMA
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import KumoDataUpdateCoordinator
from .entity import CoordinatedKumoEntity

from ..heater_cooler import (
    HeaterCoolerEntity
)

import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate.const import (
    CURRENT_HVAC_COOL, CURRENT_HVAC_DRY, CURRENT_HVAC_FAN, CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE, CURRENT_HVAC_OFF, HVAC_MODE_COOL, HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY, HVAC_MODE_HEAT, HVAC_MODE_HEAT_COOL, HVAC_MODE_OFF)
from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers.typing import HomeAssistantType

from .const import (
    CONF_ENABLE_POWER_SWITCH,
    KUMO_DATA,
    KUMO_DATA_COORDINATORS
)

_LOGGER = logging.getLogger(__name__)

CONF_NAME = "name"
CONF_ADDRESS = "address"
CONF_CONFIG = "config"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_ADDRESS): cv.string,
        vol.Required(CONF_CONFIG): cv.string,
        vol.Optional(CONF_ENABLE_POWER_SWITCH, default=False): cv.boolean
    }
)

KUMO_STATE_AUTO = "auto"
KUMO_STATE_AUTO_COOL = "autoCool"
KUMO_STATE_AUTO_HEAT = "autoHeat"
KUMO_STATE_COOL = "cool"
KUMO_STATE_HEAT = "heat"
KUMO_STATE_DRY = "dry"
KUMO_STATE_VENT = "vent"
KUMO_STATE_OFF = "off"

HA_STATE_TO_KUMO = {
    HVAC_MODE_HEAT_COOL: KUMO_STATE_AUTO,
    HVAC_MODE_COOL: KUMO_STATE_COOL,
    HVAC_MODE_HEAT: KUMO_STATE_HEAT,
    HVAC_MODE_DRY: KUMO_STATE_DRY,
    HVAC_MODE_FAN_ONLY: KUMO_STATE_VENT,
    HVAC_MODE_OFF: KUMO_STATE_OFF,
}
KUMO_STATE_TO_HA = {
    KUMO_STATE_AUTO: HVAC_MODE_HEAT_COOL,
    KUMO_STATE_AUTO_COOL: HVAC_MODE_HEAT_COOL,
    KUMO_STATE_AUTO_HEAT: HVAC_MODE_HEAT_COOL,
    KUMO_STATE_COOL: HVAC_MODE_COOL,
    KUMO_STATE_HEAT: HVAC_MODE_HEAT,
    KUMO_STATE_DRY: HVAC_MODE_DRY,
    KUMO_STATE_VENT: HVAC_MODE_FAN_ONLY,
    KUMO_STATE_OFF: HVAC_MODE_OFF,
}
KUMO_STATE_TO_HA_ACTION = {
    KUMO_STATE_AUTO: CURRENT_HVAC_IDLE,
    KUMO_STATE_AUTO_COOL: CURRENT_HVAC_COOL,
    KUMO_STATE_AUTO_HEAT: CURRENT_HVAC_HEAT,
    KUMO_STATE_COOL: CURRENT_HVAC_COOL,
    KUMO_STATE_HEAT: CURRENT_HVAC_HEAT,
    KUMO_STATE_DRY: CURRENT_HVAC_DRY,
    KUMO_STATE_VENT: CURRENT_HVAC_FAN,
    KUMO_STATE_OFF: CURRENT_HVAC_OFF,
}

async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry, async_add_entities):
    """Set up the Kumo thermostats."""
    account = hass.data[DOMAIN][entry.entry_id][KUMO_DATA].get_account()
    coordinators = hass.data[DOMAIN][entry.entry_id][KUMO_DATA_COORDINATORS]
    enable_power_switch = entry.data.get(CONF_ENABLE_POWER_SWITCH)

    if enable_power_switch:
        entities = []
        indoor_unit_serials = await hass.async_add_executor_job(account.get_indoor_units)
        for serial in indoor_unit_serials:
            coordinator = coordinators[serial]
            switch = KumoHeaterCooler(coordinator)
            entities.append(switch)
            _LOGGER.debug("Adding entity: %s", coordinator.get_device().get_name())
        if not entities:
            raise ConfigEntryNotReady("Kumo integration found no indoor units")
        async_add_entities(entities, True)

class KumoHeaterCooler(CoordinatedKumoEntity, HeaterCoolerEntity):

    def __init__(self, coordinator: KumoDataUpdateCoordinator):
        """Initialize the switch."""
        super().__init__(coordinator)
        coordinator.add_update_method(self.update)
        self._name = self._pykumo.get_name()
        _LOGGER.debug("[__init__] loaded Kumo switch %s;", self._name)

    @property
    def unique_id(self):
        """Return unique id"""
        # For backwards compatibility, this ID is considered the primary
        return self._identifier

    async def update(self):
        _LOGGER.error("[KumoHeaterCooler] update failed")
        if not self.available:
            # Get out early if it's failing
            return
