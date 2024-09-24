"""Implement a Lares door/window/motion sensor."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_ZONES, ZONE_STATUS_ALARM, ZONE_STATUS_NOT_USED


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
