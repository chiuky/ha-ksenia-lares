"""Provides support for Lares motion/door events."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DATA_ZONES, DOMAIN, ZONE_STATUS_NOT_USED
from .lares_zone_sensor import LaresZoneSensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors attached to a Lares alarm device from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    device_info = await coordinator.client.device_info()
    zone_descriptions = await coordinator.client.zone_descriptions()

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    zones = coordinator.data[DATA_ZONES]

    def _async_add_lares_sensors() -> None:
        zoneSensors = addLaresZoneSensors(
            coordinator, zones, zone_descriptions, device_info
        )
        async_add_entities(zoneSensors)

    def addLaresZoneSensors(coordinator, zones, zone_descriptions, device_info):
        entities = []
        if zones is not None:
            for idx, zone in enumerate(zones):
                if zone is not None and zone["status"] != ZONE_STATUS_NOT_USED:
                    entities.append(
                        LaresZoneSensor(
                            coordinator, idx, zone_descriptions[idx], device_info
                        )
                    )
        return entities

    _async_add_lares_sensors()
