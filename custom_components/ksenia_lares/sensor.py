"""Provide support for Lares partitions."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DATA_PARTITIONS, DATA_TEMPERATURES, DOMAIN
from .lares_partition_sensor import LaresPartitionSensor
from .lares_temperature_sensor import LaresTemperatureSensor


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors attached to a Lares alarm device from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    device_info = await coordinator.client.device_info()
    partition_descriptions = await coordinator.client.partition_descriptions()

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    def addLaresSensors() -> None:
        partitionSensors = addLaresPartitionSensors(
            coordinator, partition_descriptions, device_info
        )
        temperatureSensors = addLaresTemperatureSensors(coordinator, device_info)
        partitionSensors.extend(temperatureSensors)
        async_add_entities(partitionSensors)

    def addLaresPartitionSensors(coordinator, partition_descriptions, device_info):
        entities = []
        if coordinator.data[DATA_PARTITIONS] is not None:
            for idx, partition in enumerate(coordinator.data[DATA_PARTITIONS]):
                if partition is not None and partition_descriptions[idx] is not None:
                    entities.append(
                        LaresPartitionSensor(
                            coordinator, idx, partition_descriptions[idx], device_info
                        )
                    )
        return entities

    def addLaresTemperatureSensors(coordinator, device_info):
        entities = []
        if coordinator.data[DATA_TEMPERATURES] is not None:
            for idx, temperature in enumerate(coordinator.data[DATA_TEMPERATURES]):
                if temperature is not None and temperature["description"] is not None:
                    entities.append(
                        LaresTemperatureSensor(
                            coordinator,
                            idx,
                            temperature["description"],
                            temperature["temperatureValue"],
                            device_info,
                        )
                    )
        return entities

    addLaresSensors()
