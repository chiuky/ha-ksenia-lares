"""Provide support for Lares partitions."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_COORDINATOR,
    DATA_PARTITIONS,
    DATA_TEMPERATURES,
    DOMAIN,
)
from .lares_partition_sensor import LaresPartitionSensor
from .lares_temperature_sensor import LaresTemperatureSensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors attached to a Lares alarm device from a config entry."""
    _LOGGER.debug("Setting up Lares sensors")

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]

    try:
        device_info = await coordinator.client.device_info()
        if device_info is None:
            _LOGGER.error("Failed to get device info for sensors")
            return

        partition_descriptions = await coordinator.client.partition_descriptions()
        if partition_descriptions is None:
            _LOGGER.warning("No partition descriptions available")
            partition_descriptions = []

        # Fetch initial data so we have data when entities subscribe
        await coordinator.async_refresh()
    except (KeyError, AttributeError, TypeError) as err:
        _LOGGER.error(
            "Invalid data structure setting up sensors: %s", err, exc_info=True
        )
        return
    except (OSError, TimeoutError) as err:
        _LOGGER.error("Network error setting up sensors: %s", err)
        return
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Unexpected error setting up sensors: %s", err, exc_info=True)
        return

    def _add_lares_sensors() -> None:
        partition_sensors = _add_lares_partition_sensors(
            coordinator, partition_descriptions, device_info
        )
        temperature_sensors = _add_lares_temperature_sensors(coordinator, device_info)
        partition_sensors.extend(temperature_sensors)

        if partition_sensors:
            _LOGGER.info(
                "Adding %d sensors (%d partitions, %d temperatures)",
                len(partition_sensors),
                len(partition_sensors) - len(temperature_sensors),
                len(temperature_sensors),
            )
            async_add_entities(partition_sensors)
        else:
            _LOGGER.info("No sensors to add")

    def _add_lares_partition_sensors(
        coordinator, partition_descriptions: list[str] | None, device_info: dict
    ) -> list:
        entities = []
        partitions = coordinator.data.get(DATA_PARTITIONS)
        if partitions is not None and partition_descriptions is not None:
            for idx, partition in enumerate(partitions):
                try:
                    if (
                        partition is not None
                        and idx < len(partition_descriptions)
                        and partition_descriptions[idx]
                    ):
                        entities.append(
                            LaresPartitionSensor(
                                coordinator,
                                idx,
                                partition_descriptions[idx],
                                device_info,
                            )
                        )
                except (IndexError, KeyError) as err:
                    _LOGGER.warning("Error creating partition sensor %d: %s", idx, err)
                    continue
        return entities

    def _add_lares_temperature_sensors(coordinator, device_info: dict) -> list:
        entities = []
        temperatures = coordinator.data.get(DATA_TEMPERATURES)
        if temperatures is not None:
            for idx, temperature in enumerate(temperatures):
                try:
                    if temperature is not None and temperature.get("description"):
                        entities.append(
                            LaresTemperatureSensor(
                                coordinator,
                                idx,
                                temperature["description"],
                                temperature.get("temperatureValue"),
                                device_info,
                            )
                        )
                except (KeyError, TypeError) as err:
                    _LOGGER.warning(
                        "Error creating temperature sensor %d: %s", idx, err
                    )
                    continue
        return entities

    _add_lares_sensors()
