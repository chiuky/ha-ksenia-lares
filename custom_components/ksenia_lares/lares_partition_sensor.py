"""Implement  a Lares partition sensor."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_PARTITIONS,
    PARTITION_STATUS_ALARM,
    PARTITION_STATUS_ARMED,
    PARTITION_STATUS_ARMED_IMMEDIATE,
    PARTITION_STATUS_ARMING,
    PARTITION_STATUS_DISARMED,
    PARTITION_STATUS_PENDING,
)


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

    def get_status(self) -> str | None:
        """Return the status of this partition."""
        return self._coordinator.data[DATA_PARTITIONS][self._idx]["status"]
