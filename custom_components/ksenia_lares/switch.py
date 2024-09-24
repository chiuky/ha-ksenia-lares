"""Provide support for Lares zone bypass."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_PIN,
    DATA_COORDINATOR,
    DATA_OUTPUTS,
    DATA_ZONES,
    DOMAIN,
    ZONE_STATUS_NOT_USED,
)
from .lares_bypass_switch_sensor import LaresBypassSwitchSensor
from .lares_output_sensor import LaresOutputSensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up zone bypass switches for zones in the Lares alarm device from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    device_info = await coordinator.client.device_info()
    zone_descriptions = await coordinator.client.zone_descriptions()
    output_descriptions = await coordinator.client.output_descriptions()
    options = {CONF_PIN: config_entry.options.get(CONF_PIN)}

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    zones = coordinator.data[DATA_ZONES]
    outputs = coordinator.data[DATA_OUTPUTS]

    def _async_add_laresBypassSwitch() -> None:
        entities = []
        zoneSensors = filterZoneSensors(
            coordinator, zones, zone_descriptions, device_info
        )
        outputSensors = filterOutputSensors(
            coordinator, outputs, output_descriptions, device_info
        )
        entities.extend(zoneSensors)
        entities.extend(outputSensors)
        async_add_entities(entities)

    def filterZoneSensors(coordinator, zones, zone_descriptions, device_info):
        entities = []
        for idx, zone in enumerate(zones):
            if zone is not None and zone["status"] != ZONE_STATUS_NOT_USED:
                entities.append(
                    LaresBypassSwitchSensor(
                        coordinator, idx, zone_descriptions[idx], device_info, options
                    )
                )
        return entities

    def filterOutputSensors(coordinator, outputs, output_descriptions, device_info):
        entities = []
        for idx, output in enumerate(outputs):
            if output is not None and output["type"] != ZONE_STATUS_NOT_USED:
                entities.append(
                    LaresOutputSensor(
                        coordinator, idx, output_descriptions[idx], device_info, options
                    )
                )
        return entities

    _async_add_laresBypassSwitch()
