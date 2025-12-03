"""Provides device conditions for Ksenia Lares."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.const import (
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    condition,
    config_validation as cv,
    entity_registry as er,
)
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Condition types for alarm control panel
CONDITION_ALARM_TRIGGERED = "is_triggered"
CONDITION_ALARM_ARMED_AWAY = "is_armed_away"
CONDITION_ALARM_ARMED_HOME = "is_armed_home"
CONDITION_ALARM_ARMED_NIGHT = "is_armed_night"
CONDITION_ALARM_DISARMED = "is_disarmed"
CONDITION_ALARM_ARMING = "is_arming"
CONDITION_ALARM_PENDING = "is_pending"

# Condition types for zones
CONDITION_ZONE_OPENED = "is_opened"
CONDITION_ZONE_CLOSED = "is_closed"
CONDITION_ZONE_BYPASSED = "is_bypassed"
CONDITION_ZONE_NOT_BYPASSED = "is_not_bypassed"

# Condition types for outputs
CONDITION_OUTPUT_ON = "is_on"
CONDITION_OUTPUT_OFF = "is_off"

ALARM_CONDITION_TYPES = {
    CONDITION_ALARM_TRIGGERED,
    CONDITION_ALARM_ARMED_AWAY,
    CONDITION_ALARM_ARMED_HOME,
    CONDITION_ALARM_ARMED_NIGHT,
    CONDITION_ALARM_DISARMED,
    CONDITION_ALARM_ARMING,
    CONDITION_ALARM_PENDING,
}

ZONE_CONDITION_TYPES = {
    CONDITION_ZONE_OPENED,
    CONDITION_ZONE_CLOSED,
    CONDITION_ZONE_BYPASSED,
    CONDITION_ZONE_NOT_BYPASSED,
}

OUTPUT_CONDITION_TYPES = {
    CONDITION_OUTPUT_ON,
    CONDITION_OUTPUT_OFF,
}

CONDITION_SCHEMA = cv.DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required(CONF_TYPE): vol.In(
            ALARM_CONDITION_TYPES | ZONE_CONDITION_TYPES | OUTPUT_CONDITION_TYPES
        ),
    }
)


async def async_get_conditions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device conditions for Ksenia Lares devices."""
    registry = er.async_get(hass)
    conditions = []

    # Get all entities for this device
    entries = er.async_entries_for_device(registry, device_id)

    for entry in entries:
        # Add alarm control panel conditions
        if entry.domain == "alarm_control_panel":
            conditions.extend(
                [
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_ALARM_TRIGGERED,
                    },
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_ALARM_ARMED_AWAY,
                    },
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_ALARM_ARMED_HOME,
                    },
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_ALARM_ARMED_NIGHT,
                    },
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_ALARM_DISARMED,
                    },
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_ALARM_ARMING,
                    },
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_ALARM_PENDING,
                    },
                ]
            )

        # Add zone (binary sensor) conditions
        elif entry.domain == "binary_sensor":
            conditions.extend(
                [
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_ZONE_OPENED,
                    },
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_ZONE_CLOSED,
                    },
                ]
            )

        # Add zone bypass conditions (switch)
        elif entry.domain == "switch" and "bypass" in entry.entity_id.lower():
            conditions.extend(
                [
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_ZONE_BYPASSED,
                    },
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_ZONE_NOT_BYPASSED,
                    },
                ]
            )

        # Add output conditions (switch)
        elif entry.domain == "switch" and "output" in entry.entity_id.lower():
            conditions.extend(
                [
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_OUTPUT_ON,
                    },
                    {
                        CONF_CONDITION: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.id,
                        CONF_TYPE: CONDITION_OUTPUT_OFF,
                    },
                ]
            )

    return conditions


@callback
def async_condition_from_config(
    hass: HomeAssistant, config: ConfigType
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    registry = er.async_get(hass)
    entity_id = er.async_resolve_entity_id(registry, config[CONF_ENTITY_ID])

    if entity_id is None:
        _LOGGER.warning("Entity %s not found in registry", config[CONF_ENTITY_ID])

        @callback
        def test_condition_internal(
            _hass: HomeAssistant, _variables: TemplateVarsType
        ) -> bool:
            """Test if condition is true."""
            return False

        return test_condition_internal

    condition_type = config[CONF_TYPE]

    # Map condition types to state checks
    @callback
    def test_condition(hass: HomeAssistant, _variables: TemplateVarsType) -> bool:
        """Test if condition is true."""
        state = hass.states.get(entity_id)
        if state is None:
            return False

        # Alarm control panel conditions
        if condition_type == CONDITION_ALARM_TRIGGERED:
            return state.state == "triggered"
        elif condition_type == CONDITION_ALARM_ARMED_AWAY:
            return state.state == "armed_away"
        elif condition_type == CONDITION_ALARM_ARMED_HOME:
            return state.state == "armed_home"
        elif condition_type == CONDITION_ALARM_ARMED_NIGHT:
            return state.state == "armed_night"
        elif condition_type == CONDITION_ALARM_DISARMED:
            return state.state == "disarmed"
        elif condition_type == CONDITION_ALARM_ARMING:
            return state.state == "arming"
        elif condition_type == CONDITION_ALARM_PENDING:
            return state.state == "pending"

        # Zone conditions
        elif condition_type == CONDITION_ZONE_OPENED:
            return state.state == "on"
        elif condition_type == CONDITION_ZONE_CLOSED:
            return state.state == "off"

        # Bypass/Output conditions
        elif (
            condition_type == CONDITION_ZONE_BYPASSED
            or condition_type == CONDITION_OUTPUT_ON
        ):
            return state.state == "on"
        elif (
            condition_type == CONDITION_ZONE_NOT_BYPASSED
            or condition_type == CONDITION_OUTPUT_OFF
        ):
            return state.state == "off"

        return False

    return test_condition


async def async_get_condition_capabilities(
    _hass: HomeAssistant, _config: ConfigType
) -> dict[str, vol.Schema]:
    """List condition capabilities."""
    return {}
