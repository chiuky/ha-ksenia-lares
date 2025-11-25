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
    _LOGGER.debug("Setting up Lares switches")

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]

    try:
        device_info = await coordinator.client.device_info()
        if device_info is None:
            _LOGGER.error("Failed to get device info for switches")
            return

        zone_descriptions = await coordinator.client.zone_descriptions()
        if zone_descriptions is None:
            _LOGGER.warning("No zone descriptions available")
            zone_descriptions = []

        output_descriptions = await coordinator.client.output_descriptions()
        if output_descriptions is None:
            _LOGGER.warning("No output descriptions available")
            output_descriptions = []

        options = {CONF_PIN: config_entry.options.get(CONF_PIN)}

        # Fetch initial data so we have data when entities subscribe
        await coordinator.async_refresh()

        zones = coordinator.data.get(DATA_ZONES)
        outputs = coordinator.data.get(DATA_OUTPUTS)

        if zones is None and outputs is None:
            _LOGGER.warning("No zones or outputs data available, skipping switch setup")
            return
    except Exception as err:
        _LOGGER.error("Error setting up switches: %s", err, exc_info=True)
        return

    def _async_add_lares_bypass_switch() -> None:
        entities = []
        zone_sensors = _filter_zone_sensors(
            coordinator, zones, zone_descriptions, device_info
        )
        output_sensors = _filter_output_sensors(
            coordinator, outputs, output_descriptions, device_info
        )
        entities.extend(zone_sensors)
        entities.extend(output_sensors)

        if entities:
            _LOGGER.info("Adding %d switches (%d zones, %d outputs)",
                        len(entities),
                        len(zone_sensors),
                        len(output_sensors))
            async_add_entities(entities)
        else:
            _LOGGER.info("No switches to add")

    def _filter_zone_sensors(
        coordinator, zones: list[dict] | None, zone_descriptions: list[str] | None, device_info: dict
    ) -> list:
        entities = []
        if zones is not None and zone_descriptions is not None:
            for idx, zone in enumerate(zones):
                try:
                    if zone is not None and zone.get("status") != ZONE_STATUS_NOT_USED:
                        description = zone_descriptions[idx] if idx < len(zone_descriptions) else f"Zone {idx}"
                        entities.append(
                            LaresBypassSwitchSensor(
                                coordinator, idx, description, device_info, options
                            )
                        )
                except (IndexError, KeyError) as err:
                    _LOGGER.warning("Error creating zone switch %d: %s", idx, err)
                    continue
        return entities

    def _filter_output_sensors(
        coordinator, outputs: list[dict] | None, output_descriptions: list[str] | None, device_info: dict
    ) -> list:
        entities = []
        if outputs is not None and output_descriptions is not None:
            for idx, output in enumerate(outputs):
                try:
                    if output is not None and output.get("type") != ZONE_STATUS_NOT_USED:
                        description = output_descriptions[idx] if idx < len(output_descriptions) else f"Output {idx}"
                        entities.append(
                            LaresOutputSensor(
                                coordinator, idx, description, device_info, options
                            )
                        )
                except (IndexError, KeyError) as err:
                    _LOGGER.warning("Error creating output switch %d: %s", idx, err)
                    continue
        return entities

    _async_add_lares_bypass_switch()
