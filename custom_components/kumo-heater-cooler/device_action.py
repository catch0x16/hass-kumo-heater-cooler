"""Provides device automations for heater/cooler."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components.device_automation import (
    async_get_entity_registry_entry_or_raise,
    async_validate_entity_schema,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from .const import (
    Active,
    TargetState,

    ATTR_ACTIVE,
    ATTR_TARGET_STATE,

    DOMAIN,

    SERVICE_SET_ACTIVE,
    SERVICE_SET_TARGET_STATE
)

ACTION_TYPES = {SERVICE_SET_ACTIVE, SERVICE_SET_TARGET_STATE}

SET_ACTIVE_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): "set_active",
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(ATTR_ACTIVE): vol.In(Active),
    }
)

SET_TARGET_STATE_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): "set_target_state",
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(ATTR_TARGET_STATE): vol.In(TargetState),
    }
)

_ACTION_SCHEMA = vol.Any(SET_ACTIVE_SCHEMA, SET_TARGET_STATE_SCHEMA)


async def async_validate_action_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate config."""
    return async_validate_entity_schema(hass, config, _ACTION_SCHEMA)


async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device actions for heater/cooler devices."""
    registry = er.async_get(hass)
    actions = []

    # Get all the integrations entities for this device
    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        # TODO: Add more features
        # supported_features = get_supported_features(hass, entry.entity_id)

        base_action = {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.id,
        }

        actions.append({**base_action, CONF_TYPE: SERVICE_SET_ACTIVE})
        actions.append({**base_action, CONF_TYPE: SERVICE_SET_TARGET_STATE})
        # TODO: Add more features
        # if supported_features & const.SUPPORT_PRESET_MODE:

    return actions


async def async_call_action_from_config(
    hass: HomeAssistant,
    config: ConfigType,
    variables: TemplateVarsType,
    context: Context | None,
) -> None:
    """Execute a device action."""
    service_data = {ATTR_ENTITY_ID: config[CONF_ENTITY_ID]}

    if config[CONF_TYPE] == SERVICE_SET_ACTIVE:
        service = SERVICE_SET_ACTIVE
        service_data[ATTR_ACTIVE] = config[ATTR_ACTIVE]
    elif config[CONF_TYPE] == SERVICE_SET_TARGET_STATE:
        service =SERVICE_SET_TARGET_STATE
        service_data[ATTR_TARGET_STATE] = config[ATTR_TARGET_STATE]

    await hass.services.async_call(
        DOMAIN, service, service_data, blocking=True, context=context
    )


async def async_get_action_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """List action capabilities."""
    action_type = config[CONF_TYPE]

    fields = {}

    if action_type == SERVICE_SET_ACTIVE:
        fields[vol.Required(ATTR_ACTIVE)] = vol.In(Active)
    elif action_type == SERVICE_SET_TARGET_STATE:
        fields[vol.Required(ATTR_TARGET_STATE)] = vol.In(TargetState)

    return {"extra_fields": vol.Schema(fields)}
