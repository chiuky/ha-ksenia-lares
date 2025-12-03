"""Provides device triggers for Ksenia Lares."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import state as state_trigger
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Trigger types for alarm control panel
TRIGGER_ALARM_TRIGGERED = "alarm_triggered"
TRIGGER_ALARM_ARMED_AWAY = "alarm_armed_away"
TRIGGER_ALARM_ARMED_HOME = "alarm_armed_home"
TRIGGER_ALARM_ARMED_NIGHT = "alarm_armed_night"
TRIGGER_ALARM_DISARMED = "alarm_disarmed"
TRIGGER_ALARM_ARMING = "alarm_arming"
TRIGGER_ALARM_PENDING = "alarm_pending"

# Trigger types for zones (binary sensors)
TRIGGER_ZONE_OPENED = "zone_opened"
TRIGGER_ZONE_CLOSED = "zone_closed"
TRIGGER_ZONE_ALARM = "zone_alarm"

ALARM_TRIGGER_TYPES = {
    TRIGGER_ALARM_TRIGGERED,
    TRIGGER_ALARM_ARMED_AWAY,
    TRIGGER_ALARM_ARMED_HOME,
    TRIGGER_ALARM_ARMED_NIGHT,
    TRIGGER_ALARM_DISARMED,
    TRIGGER_ALARM_ARMING,
    TRIGGER_ALARM_PENDING,
}

ZONE_TRIGGER_TYPES = {
    TRIGGER_ZONE_OPENED,
    TRIGGER_ZONE_CLOSED,
    TRIGGER_ZONE_ALARM,
}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(CONF_TYPE): vol.In(ALARM_TRIGGER_TYPES | ZONE_TRIGGER_TYPES),
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device triggers for Ksenia Lares devices."""
    registry = er.async_get(hass)
    triggers = []

    # Get all entities for this device
    entries = er.async_entries_for_device(registry, device_id)

    for entry in entries:
        # Add alarm control panel triggers
        if entry.domain == "alarm_control_panel":
            triggers.extend(
                [
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: TRIGGER_ALARM_TRIGGERED,
                    },
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: TRIGGER_ALARM_ARMED_AWAY,
                    },
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: TRIGGER_ALARM_ARMED_HOME,
                    },
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: TRIGGER_ALARM_ARMED_NIGHT,
                    },
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: TRIGGER_ALARM_DISARMED,
                    },
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: TRIGGER_ALARM_ARMING,
                    },
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: TRIGGER_ALARM_PENDING,
                    },
                ]
            )

        # Add zone (binary sensor) triggers
        elif entry.domain == "binary_sensor":
            triggers.extend(
                [
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: TRIGGER_ZONE_OPENED,
                    },
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: TRIGGER_ZONE_CLOSED,
                    },
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: TRIGGER_ZONE_ALARM,
                    },
                ]
            )

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    registry = er.async_get(hass)
    entity_id = er.async_resolve_entity_id(registry, config[CONF_ENTITY_ID])

    if entity_id is None:
        _LOGGER.warning("Entity %s not found in registry", config[CONF_ENTITY_ID])
        return lambda: None

    trigger_type = config[CONF_TYPE]

    # Map trigger types to state changes
    state_config = {
        CONF_PLATFORM: "state",
        CONF_ENTITY_ID: entity_id,
    }

    if trigger_type == TRIGGER_ALARM_TRIGGERED:
        state_config["to"] = "triggered"
    elif trigger_type == TRIGGER_ALARM_ARMED_AWAY:
        state_config["to"] = "armed_away"
    elif trigger_type == TRIGGER_ALARM_ARMED_HOME:
        state_config["to"] = "armed_home"
    elif trigger_type == TRIGGER_ALARM_ARMED_NIGHT:
        state_config["to"] = "armed_night"
    elif trigger_type == TRIGGER_ALARM_DISARMED:
        state_config["to"] = "disarmed"
    elif trigger_type == TRIGGER_ALARM_ARMING:
        state_config["to"] = "arming"
    elif trigger_type == TRIGGER_ALARM_PENDING:
        state_config["to"] = "pending"
    elif trigger_type == TRIGGER_ZONE_OPENED:
        state_config["to"] = "on"
    elif trigger_type == TRIGGER_ZONE_CLOSED:
        state_config["to"] = "off"
    elif trigger_type == TRIGGER_ZONE_ALARM:
        state_config["to"] = "on"
        # Could also check for alarm attribute

    state_config = await state_trigger.async_validate_trigger_config(hass, state_config)
    return await state_trigger.async_attach_trigger(
        hass, state_config, action, trigger_info, platform_type="device"
    )


async def async_get_trigger_capabilities(
    _hass: HomeAssistant, _config: ConfigType
) -> dict[str, vol.Schema]:
    """List trigger capabilities."""
    return {}
