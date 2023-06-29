"""HomeAssistant climate component for KumoCloud connected HVAC units."""
import logging

import voluptuous as vol
from homeassistant.components.climate import PLATFORM_SCHEMA
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import KumoDataUpdateCoordinator
from .entity import CoordinatedKumoEntity

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass

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
            switch = KumoSwitch(coordinator)
            entities.append(switch)
            _LOGGER.debug("Adding entity: %s", coordinator.get_device().get_name())
        if not entities:
            raise ConfigEntryNotReady("Kumo integration found no indoor units")
        async_add_entities(entities, True)

class KumoSwitch(CoordinatedKumoEntity, SwitchEntity):

    def __init__(self, coordinator: KumoDataUpdateCoordinator):
        """Initialize the switch."""
        super().__init__(coordinator)
        coordinator.add_update_method(self.update)
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._name = self._pykumo.get_name()
        self._last_hvac_mode = None
        self._hvac_mode = None
        self._attr_is_on = None
        _LOGGER.debug("[__init__] loaded Kumo switch %s;", self._name)

    @property
    def unique_id(self):
        """Return unique id"""
        # For backwards compatibility, this ID is considered the primary
        return self._identifier

    async def update(self):
        if not self.available:
            # Get out early if it's failing
            return
        self._update_hvac_mode()

    def _update_hvac_mode(self):
        """Refresh cached hvac mode."""
        mode = self._pykumo.get_mode()
        try:
            hvac_mode = KUMO_STATE_TO_HA[mode]
        except KeyError:
            hvac_mode = None
        
        if hvac_mode is not None:
            if self._hvac_mode is not None and self._hvac_mode is not HVAC_MODE_OFF:
                self._last_hvac_mode = self._hvac_mode
            self._hvac_mode = hvac_mode
            self._attr_is_on = not self._hvac_mode in {None, HVAC_MODE_OFF}
            _LOGGER.debug("[_update_hvac_mode] mode updated %s: %s -> %s", self._name, self._hvac_mode, self._last_hvac_mode)


    def async_turn_on(self) -> None:
        if self._last_hvac_mode is not None and self._last_hvac_mode is not HVAC_MODE_OFF:
            self.async_set_hvac_mode(self._last_hvac_mode)
            _LOGGER.debug("[async_turn_on] turned on %s: %s -> %s", self._name, self._hvac_mode, self._last_hvac_mode)
        else:
            _LOGGER.debug("[async_turn_on] no-op %s: %s -> %s", self._name, self._hvac_mode, self._last_hvac_mode)

    def async_turn_off(self) -> None:
        self.async_set_hvac_mode(HVAC_MODE_OFF)
        _LOGGER.debug("[async_turn_off] turned off %s: %s -> %s", self._name, self._hvac_mode, self._last_hvac_mode)

    def async_set_hvac_mode(self, hvac_mode):
        try:
            mode = HA_STATE_TO_KUMO[hvac_mode]
        except KeyError:
            mode = "off"

        if not self.available:
            _LOGGER.warning("Kumo %s is not available", self._name)
            return

        response = self._pykumo.set_mode(mode)
        _LOGGER.debug(
            "Kumo %s set mode %s response: %s", self._name, hvac_mode, response
        )