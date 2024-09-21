"""Provides support for Lares motion/door events."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DATA_PARTITIONS,
    DATA_ZONES,
    DOMAIN,
    PARTITION_STATUS_ALARM,
    PARTITION_STATUS_ARMED,
    PARTITION_STATUS_ARMED_IMMEDIATE,
    PARTITION_STATUS_ARMING,
    PARTITION_STATUS_DISARMED,
    PARTITION_STATUS_PENDING,
    ZONE_STATUS_ALARM,
    ZONE_STATUS_NOT_USED,
)

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
        for idx, zone in enumerate(zones):
            if zone is not None and zone["status"] != ZONE_STATUS_NOT_USED:
                entities.append(
                    LaresZoneSensor(
                        coordinator, idx, zone_descriptions[idx], device_info
                    )
                )
        return entities

    _async_add_lares_sensors()


class LaresZoneSensor(CoordinatorEntity, BinarySensorEntity):
    """Implement a Lares door/window/motion sensor."""

    def __init__(self, coordinator, idx, description, device_info) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._description = description
        self._idx = idx

        self._attr_device_info = device_info
        self._attr_device_class = "motion"

        # Hide sensor if it is indicated as not used
        is_used = (
            self._coordinator.data[DATA_ZONES][self._idx]["status"]
            != ZONE_STATUS_NOT_USED
        )

        self._attr_entity_registry_enabled_default = is_used
        self._attr_entity_registry_visible_default = is_used

    @property
    def unique_id(self) -> str:
        """Return Unique ID string."""
        return f"lares_zone_{self._idx}"

    @property
    def name(self) -> str:
        """Return the name of this camera."""
        return self._description

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return (
            self._coordinator.data[DATA_ZONES][self._idx]["status"] == ZONE_STATUS_ALARM
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""

        status = self._coordinator.data[DATA_ZONES][self._idx]["status"]

        return status != ZONE_STATUS_NOT_USED


class LaresSensor(CoordinatorEntity, BinarySensorEntity):
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
        return f"lares_partitions_{self._idx}"

    @property
    def name(self) -> str:
        """Return the name of this entity."""
        return self._description

    @property
    def native_value(self) -> str:
        """Return the status of this partition."""
        return self._coordinator.data[DATA_PARTITIONS][self._idx]["status"]
