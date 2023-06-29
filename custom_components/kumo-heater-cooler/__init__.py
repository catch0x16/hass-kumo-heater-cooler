"""Provides functionality to interact with heater/cooler devices."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import functools as ft
import logging
from typing import Any, final

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE
)
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.config_validation import (  # noqa: F401
    make_entity_service_schema,
)
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.temperature import display_temp as show_temp
from homeassistant.helpers.typing import ConfigType
from homeassistant.util.unit_conversion import TemperatureConverter
from homeassistant.const import ATTR_TEMPERATURE

from .const import (
    Active,
    CurrentState,
    TargetState,

    HeaterCoolerEntityFeature,

    ATTR_ACTIVE,
    ATTR_TARGET_STATE,
    ATTR_CURRENT_STATE,
    ATTR_CURRENT_TEMPERATURE,

    DOMAIN,

    SERVICE_SET_ACTIVE,
    SERVICE_SET_TARGET_STATE,
    SERVICE_SET_TEMPERATURE,
)

DEFAULT_MIN_TEMP = 7
DEFAULT_MAX_TEMP = 35
DEFAULT_MIN_HUMIDITY = 30
DEFAULT_MAX_HUMIDITY = 99

ENTITY_ID_FORMAT = DOMAIN + ".{}"
SCAN_INTERVAL = timedelta(seconds=60)

CONVERTIBLE_ATTRIBUTE = []

_LOGGER = logging.getLogger(__name__)

SET_TEMPERATURE_SCHEMA = vol.All(
    cv.has_at_least_one_key(
        ATTR_TEMPERATURE
    ),
    make_entity_service_schema(
        {
            vol.Optional(ATTR_ACTIVE): vol.Coerce(Active),
            vol.Optional(ATTR_TARGET_STATE): vol.Coerce(TargetState)
        }
    ),
)

# mypy: disallow-any-generics


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up heater/cooler entities."""
    component = hass.data[DOMAIN] = EntityComponent[HeaterCoolerEntity](
        _LOGGER, DOMAIN, hass, SCAN_INTERVAL
    )
    await component.async_setup(config)

    _LOGGER.warning("Heater/Cooler service starting")

    component.async_register_entity_service(
        SERVICE_SET_ACTIVE,
        {vol.Required(ATTR_ACTIVE): vol.Coerce(Active)},
        "async_set_active",
    )
    component.async_register_entity_service(
        SERVICE_SET_TARGET_STATE,
        {vol.Required(ATTR_TARGET_STATE): cv.string},
        "async_set_target_state",
    )
    component.async_register_entity_service(
        SERVICE_SET_TEMPERATURE,
        SET_TEMPERATURE_SCHEMA,
        async_service_temperature_set,
        [
            HeaterCoolerEntityFeature.TARGET_TEMPERATURE
        ],
    )

    _LOGGER.warning("Heater/Cooler service started")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    component: EntityComponent[HeaterCoolerEntity] = hass.data[DOMAIN]
    return await component.async_setup_entry(entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    component: EntityComponent[HeaterCoolerEntity] = hass.data[DOMAIN]
    return await component.async_unload_entry(entry)


@dataclass
class HeaterCoolerEntityDescription(EntityDescription):
    """A class that describes heater/cooler entities."""

class HeaterCoolerEntity(Entity):
    """Base class for heater/cooler entities."""

    entity_description: HeaterCoolerEntityDescription
    _attr_current_temperature: float | None = None
    _attr_target_temperature: float | None = None
    _attr_active: Active | None = None
    _attr_current_state: CurrentState | None
    _attr_target_state: TargetState | None
    _attr_supported_features: HeaterCoolerEntityFeature = HeaterCoolerEntityFeature(0)
    _attr_temperature_unit: str

    @final
    @property
    def state(self) -> str | None:
        """Return the current state."""
        if self.current_state is None:
            return None
        if not isinstance(self.current_state, CurrentState):
            return CurrentState(self.current_state).value
        return self.current_state.value

    @property
    def capability_attributes(self) -> dict[str, Any] | None:
        """Return the capability attributes."""
        data: dict[str, Any] = {
            ATTR_ACTIVE: self._attr_active,
            ATTR_TARGET_STATE: self._attr_target_state,
            ATTR_CURRENT_STATE: self._attr_current_state
        }

        return data

    @final
    @property
    def state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        supported_features = self.supported_features
        data: dict[str, str | float | None] = {
            ATTR_CURRENT_TEMPERATURE: show_temp(
                self.hass,
                self.current_temperature,
                self.temperature_unit,
                self.precision,
            ),
            ATTR_ACTIVE: self._attr_active,
            ATTR_CURRENT_STATE: self._attr_current_state,
            ATTR_TARGET_STATE: self._attr_target_state,
            ATTR_CURRENT_TEMPERATURE: self._attr_current_temperature
        }

        if supported_features & HeaterCoolerEntityFeature.TARGET_TEMPERATURE:
            data[ATTR_TEMPERATURE] = show_temp(
                self.hass,
                self.target_temperature,
                self.temperature_unit,
                self.precision,
            )

        return data

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement used by the platform."""
        return self._attr_temperature_unit

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._attr_current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._attr_target_temperature

    @property
    def supported_features(self) -> HeaterCoolerEntityFeature:
        """Return the list of supported features."""
        return self._attr_supported_features

    def set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        raise NotImplementedError()

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        await self.hass.async_add_executor_job(
            ft.partial(self.set_temperature, **kwargs)
        )

    def set_active(self, active: Active) -> None:
        """Set new target hvac mode."""
        raise NotImplementedError()

    async def async_set_active(self, active: Active) -> None:
        """Set new target hvac mode."""
        await self.hass.async_add_executor_job(self.set_active, active)

    def set_target_state(self, target_state: TargetState) -> None:
        """Set new target hvac mode."""
        raise NotImplementedError()

    async def async_set_target_state(self, target_state: TargetState) -> None:
        """Set new target hvac mode."""
        await self.hass.async_add_executor_job(self.set_target_state, target_state)

async def async_service_temperature_set(
    entity: HeaterCoolerEntity, service_call: ServiceCall
) -> None:
    """Handle set temperature service."""
    hass = entity.hass
    kwargs = {}

    for value, temp in service_call.data.items():
        if value in CONVERTIBLE_ATTRIBUTE:
            kwargs[value] = TemperatureConverter.convert(
                temp, hass.config.units.temperature_unit, entity.temperature_unit
            )
        else:
            kwargs[value] = temp

    await entity.async_set_temperature(**kwargs)
