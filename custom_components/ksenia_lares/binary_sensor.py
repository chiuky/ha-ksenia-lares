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
    _LOGGER.debug("Setting up Lares binary sensors")

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]

    try:
        device_info = await coordinator.client.device_info()
        if device_info is None:
            _LOGGER.error("Failed to get device info for binary sensors")
            return

        zone_descriptions = await coordinator.client.zone_descriptions()
        if zone_descriptions is None:
            _LOGGER.warning("No zone descriptions available")
            zone_descriptions = []

        # Fetch initial data so we have data when entities subscribe
        await coordinator.async_refresh()

        zones = coordinator.data.get(DATA_ZONES)
        if zones is None:
            _LOGGER.warning("No zones data available, skipping binary sensor setup")
            return
    except (KeyError, AttributeError, TypeError) as err:
        _LOGGER.error("Invalid data structure setting up binary sensors: %s", err, exc_info=True)
        return
    except (OSError, TimeoutError) as err:
        _LOGGER.error("Network error setting up binary sensors: %s", err)
        return
    except Exception as err:
        _LOGGER.error("Unexpected error setting up binary sensors: %s", err, exc_info=True)
        return

    def _async_add_lares_sensors() -> None:
        zone_sensors = _add_lares_zone_sensors(
            coordinator, zones, zone_descriptions, device_info
        )
        if zone_sensors:
            _LOGGER.info("Adding %d zone binary sensors", len(zone_sensors))
            async_add_entities(zone_sensors)
        else:
            _LOGGER.info("No zone binary sensors to add")

    def _add_lares_zone_sensors(
        coordinator,
        zones: list[dict] | None,
        zone_descriptions: list[str] | None,
        device_info: dict,
    ) -> list:
        entities = []
        if zones is not None and zone_descriptions is not None:
            for idx, zone in enumerate(zones):
                try:
                    if zone is not None and zone.get("status") != ZONE_STATUS_NOT_USED:
                        description = zone_descriptions[idx] if idx < len(zone_descriptions) else f"Zone {idx}"
                        entities.append(
                            LaresZoneSensor(
                                coordinator, idx, description, device_info
                            )
                        )
                except (IndexError, KeyError) as err:
                    _LOGGER.warning("Error creating zone sensor %d: %s", idx, err)
                    continue
        return entities

    _async_add_lares_sensors()
