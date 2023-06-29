"""Provide the device automations for heater/cooler."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components.device_automation import (
    async_get_entity_registry_entry_or_raise,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    condition,
    config_validation as cv,
    entity_registry as er,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import get_capability, get_supported_features
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from . import DOMAIN, const

from .const import (
    Active,
    CurrentState,
    TargetState,

    ATTR_ACTIVE,
    ATTR_CURRENT_STATE,
    ATTR_TARGET_STATE,

    DOMAIN
)

CONDITION_TYPES = {"is_active", "is_current_state", "is_target_state"}

ACTIVE_CONDITION = cv.DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): "is_active",
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(ATTR_ACTIVE): vol.In(Active),
    }
)

CURRENT_STATE_CONDITION = cv.DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(CONF_TYPE): "is_current_state",
        vol.Required(ATTR_CURRENT_STATE): vol.In(CurrentState),
    }
)

TARGET_STATE_CONDITION = cv.DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(CONF_TYPE): "is_current_state",
        vol.Required(ATTR_TARGET_STATE): vol.In(TargetState),
    }
)

CONDITION_SCHEMA = vol.Any(ACTIVE_CONDITION, CURRENT_STATE_CONDITION, TARGET_STATE_CONDITION)


async def async_get_conditions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device conditions for heater/cooler devices."""
    registry = er.async_get(hass)
    conditions = []

    # Get all the integrations entities for this device
    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        # supported_features = get_supported_features(hass, entry.entity_id)

        base_condition = {
            CONF_CONDITION: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.id,
        }

        conditions.append({**base_condition, CONF_TYPE: "is_active"})
        conditions.append({**base_condition, CONF_TYPE: "is_current_state"})
        conditions.append({**base_condition, CONF_TYPE: "is_target_state"})

        # if supported_features & const.SUPPORT_PRESET_MODE:

    return conditions


@callback
def async_condition_from_config(
    hass: HomeAssistant, config: ConfigType
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""

    registry = er.async_get(hass)
    entity_id = er.async_resolve_entity_id(registry, config[ATTR_ENTITY_ID])

    def test_is_state(hass: HomeAssistant, variables: TemplateVarsType) -> bool:
        """Test if an entity is a certain state."""
        if not entity_id or (state := hass.states.get(entity_id)) is None:
            return False

        if config[CONF_TYPE] == "is_current_state":
            return state.state == config[ATTR_CURRENT_STATE]

        return (
            state.attributes.get(ATTR_ACTIVE)
                == config[ATTR_ACTIVE] and
            state.attributes.get(ATTR_TARGET_STATE)
                == config[ATTR_TARGET_STATE]
        )

    return test_is_state


async def async_get_condition_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """List condition capabilities."""
    condition_type = config[CONF_TYPE]

    fields = {}

    if condition_type == "is_active":
        fields[vol.Required(ATTR_ACTIVE)] = vol.In(Active)

    elif condition_type == "is_current_state":
        fields[vol.Required(ATTR_CURRENT_STATE)] = vol.In(CurrentState)

    elif condition_type == "is_target_state":
        fields[vol.Required(ATTR_TARGET_STATE)] = vol.In(TargetState)

    return {"extra_fields": vol.Schema(fields)}
