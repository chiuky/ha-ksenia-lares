"""Provides device actions for Ksenia Lares."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Action types for alarm control panel
ACTION_ALARM_ARM_AWAY = "alarm_arm_away"
ACTION_ALARM_ARM_HOME = "alarm_arm_home"
ACTION_ALARM_ARM_NIGHT = "alarm_arm_night"
ACTION_ALARM_DISARM = "alarm_disarm"
ACTION_ALARM_TRIGGER = "alarm_trigger"

# Action types for zones and outputs
ACTION_ZONE_BYPASS = "zone_bypass"
ACTION_ZONE_UNBYPASS = "zone_unbypass"
ACTION_OUTPUT_TURN_ON = "output_turn_on"
ACTION_OUTPUT_TURN_OFF = "output_turn_off"

ALARM_ACTION_TYPES = {
    ACTION_ALARM_ARM_AWAY,
    ACTION_ALARM_ARM_HOME,
    ACTION_ALARM_ARM_NIGHT,
    ACTION_ALARM_DISARM,
    ACTION_ALARM_TRIGGER,
}

ZONE_ACTION_TYPES = {
    ACTION_ZONE_BYPASS,
    ACTION_ZONE_UNBYPASS,
}

OUTPUT_ACTION_TYPES = {
    ACTION_OUTPUT_TURN_ON,
    ACTION_OUTPUT_TURN_OFF,
}

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(CONF_TYPE): vol.In(
            ALARM_ACTION_TYPES | ZONE_ACTION_TYPES | OUTPUT_ACTION_TYPES
        ),
    }
)


async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device actions for Ksenia Lares devices."""
    registry = er.async_get(hass)
    actions = []

    # Get all entities for this device
    entries = er.async_entries_for_device(registry, device_id)

    for entry in entries:
        # Add alarm control panel actions
        if entry.domain == "alarm_control_panel":
            actions.extend(
                [
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: ACTION_ALARM_ARM_AWAY,
                    },
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: ACTION_ALARM_ARM_HOME,
                    },
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: ACTION_ALARM_ARM_NIGHT,
                    },
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: ACTION_ALARM_DISARM,
                    },
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: ACTION_ALARM_TRIGGER,
                    },
                ]
            )

        # Add zone bypass actions (switch domain)
        elif entry.domain == "switch" and "bypass" in entry.entity_id.lower():
            actions.extend(
                [
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: ACTION_ZONE_BYPASS,
                    },
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: ACTION_ZONE_UNBYPASS,
                    },
                ]
            )

        # Add output actions (switch domain)
        elif entry.domain == "switch" and "output" in entry.entity_id.lower():
            actions.extend(
                [
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: ACTION_OUTPUT_TURN_ON,
                    },
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: ACTION_OUTPUT_TURN_OFF,
                    },
                ]
            )

    return actions


async def async_call_action_from_config(
    hass: HomeAssistant,
    config: ConfigType,
    _variables: TemplateVarsType,
    context: Context | None,
) -> None:
    """Execute a device action."""
    registry = er.async_get(hass)
    entity_id = er.async_resolve_entity_id(registry, config[CONF_ENTITY_ID])

    if entity_id is None:
        _LOGGER.warning("Entity %s not found in registry", config[CONF_ENTITY_ID])
        return

    action_type = config[CONF_TYPE]
    service_data = {ATTR_ENTITY_ID: entity_id}

    # Execute alarm control panel actions
    if action_type == ACTION_ALARM_ARM_AWAY:
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_arm_away",
            service_data,
            blocking=True,
            context=context,
        )
    elif action_type == ACTION_ALARM_ARM_HOME:
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_arm_home",
            service_data,
            blocking=True,
            context=context,
        )
    elif action_type == ACTION_ALARM_ARM_NIGHT:
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_arm_night",
            service_data,
            blocking=True,
            context=context,
        )
    elif action_type == ACTION_ALARM_DISARM:
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_disarm",
            service_data,
            blocking=True,
            context=context,
        )
    elif action_type == ACTION_ALARM_TRIGGER:
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_trigger",
            service_data,
            blocking=True,
            context=context,
        )

    # Execute zone bypass actions
    elif action_type == ACTION_ZONE_BYPASS:
        await hass.services.async_call(
            "switch",
            SERVICE_TURN_ON,
            service_data,
            blocking=True,
            context=context,
        )
    elif action_type == ACTION_ZONE_UNBYPASS:
        await hass.services.async_call(
            "switch",
            SERVICE_TURN_OFF,
            service_data,
            blocking=True,
            context=context,
        )

    # Execute output actions
    elif action_type == ACTION_OUTPUT_TURN_ON:
        await hass.services.async_call(
            "switch",
            SERVICE_TURN_ON,
            service_data,
            blocking=True,
            context=context,
        )
    elif action_type == ACTION_OUTPUT_TURN_OFF:
        await hass.services.async_call(
            "switch",
            SERVICE_TURN_OFF,
            service_data,
            blocking=True,
            context=context,
        )


async def async_get_action_capabilities(
    _hass: HomeAssistant, _config: ConfigType
) -> dict[str, vol.Schema]:
    """List action capabilities."""
    return {}
