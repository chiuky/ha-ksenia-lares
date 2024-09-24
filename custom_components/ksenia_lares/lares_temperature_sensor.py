"""Implement a Lares temperature sensor."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_TEMPERATURES


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

        self._attr_unique_id = f"lares_temperature_sensor_{idx}"

        # Hide sensor if it has no description
        is_inactive = not self._description

        self._attr_entity_registry_enabled_default = not is_inactive
        self._attr_entity_registry_visible_default = not is_inactive

    @property
    def unique_id(self) -> str:
        """Return Unique ID string."""
        return f"lares_temperature_{self._idx}"

    @property
    def name(self) -> str:
        """Return the original name of this entity, based on the API xpath."""
        return self._description

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit_of_measurement."""
        return "°C"

    @property
    def native_value(self) -> str:
        """Return the value of the temperatures."""
        return self._coordinator.data[DATA_TEMPERATURES][self._idx]["temperatureValue"]
