"""Module that groups code required to handle state restore for component."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import Context, HomeAssistant, State

from .const import (
    ATTR_ACTIVE,
    ATTR_TARGET_STATE,

    DOMAIN,

    SERVICE_SET_ACTIVE,
    SERVICE_SET_TARGET_STATE,
    SERVICE_SET_TEMPERATURE,
)

async def _async_reproduce_states(
    hass: HomeAssistant,
    state: State,
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce component states."""

    async def call_service(service: str, keys: Iterable, data=None):
        """Call service with set of attributes given."""
        data = data or {}
        data["entity_id"] = state.entity_id
        for key in keys:
            if (value := state.attributes.get(key)) is not None:
                data[key] = value

        await hass.services.async_call(
            DOMAIN, service, data, blocking=True, context=context
        )

    if ATTR_ACTIVE in state.attributes:
        await call_service(SERVICE_SET_ACTIVE, [ATTR_ACTIVE])

    if ATTR_TARGET_STATE in state.attributes:
        await call_service(SERVICE_SET_TARGET_STATE, [ATTR_TARGET_STATE])

    if ATTR_TEMPERATURE in state.attributes:
        await call_service(SERVICE_SET_TEMPERATURE, [ATTR_TEMPERATURE])


async def async_reproduce_states(
    hass: HomeAssistant,
    states: Iterable[State],
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce component states."""
    await asyncio.gather(
        *(
            _async_reproduce_states(
                hass, state, context=context, reproduce_options=reproduce_options
            )
            for state in states
        )
    )
