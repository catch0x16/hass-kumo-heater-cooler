"""Describe group states."""

from homeassistant.components.group import GroupIntegrationRegistry
from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant, callback

from .const import CurrentState

@callback
def async_describe_on_off_states(
    hass: HomeAssistant, registry: GroupIntegrationRegistry
) -> None:
    """Describe group on off states."""
    registry.on_off_states(
        set(CurrentState) - {CurrentState.INACTIVE},
        STATE_OFF,
    )
