"""Component that provides support for Lares alarm  control panel."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_PARTITION_AWAY,
    CONF_PARTITION_HOME,
    CONF_PARTITION_NIGHT,
    CONF_SCENARIO_AWAY,
    CONF_SCENARIO_DISARM,
    CONF_SCENARIO_HOME,
    CONF_SCENARIO_NIGHT,
    DATA_COORDINATOR,
    DOMAIN,
)
from .lares_alarm_control_panel_entity import LaresAlarmControlPanelEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up alarm control panel of the Lares alarm device from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    device_info = await coordinator.client.device_info()
    partition_descriptions = await coordinator.client.partition_descriptions()
    scenario_descriptions = await coordinator.client.scenario_descriptions()

    options = {
        CONF_PARTITION_AWAY: config_entry.options.get(CONF_PARTITION_AWAY, []),
        CONF_PARTITION_HOME: config_entry.options.get(CONF_PARTITION_HOME, []),
        CONF_PARTITION_NIGHT: config_entry.options.get(CONF_PARTITION_NIGHT, []),
        CONF_SCENARIO_NIGHT: config_entry.options.get(CONF_SCENARIO_NIGHT, []),
        CONF_SCENARIO_HOME: config_entry.options.get(CONF_SCENARIO_HOME, []),
        CONF_SCENARIO_AWAY: config_entry.options.get(CONF_SCENARIO_AWAY, []),
        CONF_SCENARIO_DISARM: config_entry.options.get(CONF_SCENARIO_DISARM, []),
    }

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_entities(
        [
            LaresAlarmControlPanelEntity(
                coordinator,
                device_info,
                partition_descriptions,
                scenario_descriptions,
                options,
            )
        ]
    )
