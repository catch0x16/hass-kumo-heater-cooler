"""Provides device automations for heater/cooler."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import (
    numeric_state as numeric_state_trigger,
    state as state_trigger,
)
from homeassistant.const import (
    CONF_ABOVE,
    CONF_BELOW,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_FOR,
    CONF_PLATFORM,
    CONF_TYPE,
    PERCENTAGE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from homeassistant.const import 

from .const import (
    Active,
    CurrentState,
    TargetState,

    ATTR_ACTIVE,
    ATTR_CURRENT_STATE,
    ATTR_TARGET_STATE,
    ATTR_CURRENT_TEMPERATURE,

    DOMAIN
)

TRIGGER_TYPES = {
    "current_temperature_changed",
    "current_state_changed",
    "target_state_changed",
    "active_changed",
}

ACIVE_TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(CONF_TYPE): "active_changed",
        vol.Required(state_trigger.CONF_TO): vol.In(Active),
    }
)

CURRENT_STATE_TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(CONF_TYPE): "current_state_changed",
        vol.Required(state_trigger.CONF_TO): vol.In(CurrentState),
    }
)

TARGET_STATE_TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(CONF_TYPE): "target_state_changed",
        vol.Required(state_trigger.CONF_TO): vol.In(TargetState),
    }
)

CURRENT_TEMPERATURE_TRIGGER_SCHEMA = vol.All(
    DEVICE_TRIGGER_BASE_SCHEMA.extend(
        {
            vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
            vol.Required(CONF_TYPE): "current_temperature_changed",
            vol.Optional(CONF_BELOW): vol.Any(vol.Coerce(float)),
            vol.Optional(CONF_ABOVE): vol.Any(vol.Coerce(float)),
            vol.Optional(CONF_FOR): cv.positive_time_period_dict,
        }
    ),
    cv.has_at_least_one_key(CONF_BELOW, CONF_ABOVE),
)

TRIGGER_SCHEMA = vol.Any(
    ACIVE_TRIGGER_SCHEMA,
    CURRENT_STATE_TRIGGER_SCHEMA,
    TARGET_STATE_TRIGGER_SCHEMA,
    CURRENT_TEMPERATURE_TRIGGER_SCHEMA
)

async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device triggers for heater/cooler devices."""
    registry = er.async_get(hass)
    triggers = []

    # Get all the integrations entities for this device
    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        state = hass.states.get(entry.entity_id)

        # Add triggers for each entity that belongs to this integration
        base_trigger = {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.id,
        }

        triggers.append(
            {
                **base_trigger,
                CONF_TYPE: "active_changed",
            }
        )

        triggers.append(
            {
                **base_trigger,
                CONF_TYPE: "current_state_changed",
            }
        )

        triggers.append(
            {
                **base_trigger,
                CONF_TYPE: "target_state_changed",
            }
        )

        triggers.append(
            {
                **base_trigger,
                CONF_TYPE: "current_temperature_changed",
            }
        )

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    if (trigger_type := config[CONF_TYPE]) == "current_state_changed":
        state_config = {
            state_trigger.CONF_PLATFORM: "state",
            state_trigger.CONF_ENTITY_ID: config[CONF_ENTITY_ID],
            state_trigger.CONF_TO: config[state_trigger.CONF_TO],
            state_trigger.CONF_FROM: [
                value
                for value in CurrentState
                if value != config[state_trigger.CONF_TO]
            ],
        }
    
        if CONF_FOR in config:
            state_config[CONF_FOR] = config[CONF_FOR]
        state_config = await state_trigger.async_validate_trigger_config(
            hass, state_config
        )
        return await state_trigger.async_attach_trigger(
            hass, state_config, action, trigger_info, platform_type="device"
        )

    numeric_state_config = {
        numeric_state_trigger.CONF_PLATFORM: "numeric_state",
        numeric_state_trigger.CONF_ENTITY_ID: config[CONF_ENTITY_ID],
    }

    if trigger_type == "current_temperature_changed":
        numeric_state_config[
            numeric_state_trigger.CONF_VALUE_TEMPLATE
        ] = "{{ state.attributes.current_temperature }}"


    if CONF_ABOVE in config:
        numeric_state_config[CONF_ABOVE] = config[CONF_ABOVE]
    if CONF_BELOW in config:
        numeric_state_config[CONF_BELOW] = config[CONF_BELOW]
    if CONF_FOR in config:
        numeric_state_config[CONF_FOR] = config[CONF_FOR]

    numeric_state_config = await numeric_state_trigger.async_validate_trigger_config(
        hass, numeric_state_config
    )
    return await numeric_state_trigger.async_attach_trigger(
        hass, numeric_state_config, action, trigger_info, platform_type="device"
    )


async def async_get_trigger_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """List trigger capabilities."""
    trigger_type = config[CONF_TYPE]

    if trigger_type == "active_changed":
        return {}

    if trigger_type == "current_state_change":
        return {}

    if trigger_type == "target_state_change":
        return {}

    if trigger_type == "current_temperature_changed":
        unit_of_measurement: str = hass.config.units.temperature_unit
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Optional(
                        CONF_ABOVE, description={"suffix": unit_of_measurement}
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_BELOW, description={"suffix": unit_of_measurement}
                    ): vol.Coerce(float),
                    vol.Optional(CONF_FOR): cv.positive_time_period_dict,
                }
            )
        }

    return {}
