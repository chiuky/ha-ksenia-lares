"""Provide support for Lares partitions."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DATA_PARTITIONS,
    DATA_TEMPERATURES,
    DOMAIN,
    PARTITION_STATUS_ALARM,
    PARTITION_STATUS_ARMED,
    PARTITION_STATUS_ARMED_IMMEDIATE,
    PARTITION_STATUS_ARMING,
    PARTITION_STATUS_DISARMED,
    PARTITION_STATUS_PENDING,
)


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


class LaresPartitionSensor(CoordinatorEntity, SensorEntity):
    """Implement  a Lares partition sensor."""

    def __init__(self, coordinator, idx, description, device_info) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._description = description
        self._idx = idx

        self._attr_icon = "mdi:shield"
        self._attr_device_info = device_info
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = [
            PARTITION_STATUS_DISARMED,
            PARTITION_STATUS_ARMED,
            PARTITION_STATUS_ARMED_IMMEDIATE,
            PARTITION_STATUS_ARMING,
            PARTITION_STATUS_PENDING,
            PARTITION_STATUS_ALARM,
        ]

        # Hide sensor if it has no description
        is_inactive = not self._description

        self._attr_entity_registry_enabled_default = not is_inactive
        self._attr_entity_registry_visible_default = not is_inactive

    @property
    def unique_id(self) -> str:
        """Return Unique ID string."""
        return f"lares_partition_{self._idx}"

    @property
    def name(self) -> str:
        """Return the name of this entity."""
        return self._description

    @property
    def native_value(self) -> str:
        """Return the status of this partition."""
        return self._coordinator.data[DATA_PARTITIONS][self._idx]["status"]


class LaresTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Implement a Lares temperature sensor."""

    def __init__(
        self, coordinator, idx, description, state: float | str | None, device_info
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._description = description
        self._idx = idx

        self._attr_icon = "mdi:temperature-celsius"
        self._attr_device_info = device_info
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self.attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

        self._attr_native_value = state

        self._attr_unique_id = f"larese_temperature_sensor_{idx}"

        # Hide sensor if it has no description
        is_inactive = not self._description

        self._attr_entity_registry_enabled_default = not is_inactive
        self._attr_entity_registry_visible_default = not is_inactive

    @property
    def unique_id(self) -> str:
        """Return Unique ID string."""
        return f"lares_temperature_sensor_{self._idx}"

    @property
    def name(self) -> str:
        """Return the name of this entity."""
        return self._description

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit_of_measurement."""
        return "°C"

    @property
    def native_value(self) -> str:
        """Return the status of this partition."""
        return self._coordinator.data[DATA_TEMPERATURES][self._idx]["temperatureValue"]
