"""Implement of a Lares output switch."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_PIN, DATA_OUTPUTS, OUTPUT_STATUS_ON, ZONE_STATUS_NOT_USED
from .coordinator import LaresDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class LaresOutputSensor(CoordinatorEntity, SwitchEntity):
    """Implement of a Lares output switch."""

    _attr_translation_key = "output"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:lightbulb"

    def __init__(
        self,
        coordinator: LaresDataUpdateCoordinator,
        idx: int,
        description: str,
        device_info: dict,
        options: dict,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._idx = idx
        self._pin = options[CONF_PIN]

        self._attr_unique_id = f"lares_output_{self._idx}"
        self._attr_device_info = device_info
        self._attr_name = description
        self._attr_has_entity_name = True

        is_used = (
            self._coordinator.data[DATA_OUTPUTS][self._idx]["type"]
            != ZONE_STATUS_NOT_USED
        )

        self._attr_entity_registry_enabled_default = is_used
        self._attr_entity_registry_visible_default = is_used

    def get_status(self) -> bool | None:
        """Return true if the output is on."""
        status = self._coordinator.data[DATA_OUTPUTS][self._idx]["status"]
        isOn = status == OUTPUT_STATUS_ON
        if isOn:
            self._attr_icon = "mdi:lightbulb-on"
        else:
            self._attr_icon = "mdi:lightbulb-off"

        return isOn

    @property
    def is_on(self) -> bool | None:
        """Set a property related to the status."""
        return self.get_status()

    def turn_on(self, **kwargs: Any) -> None:
        """Switch on the output (sync wrapper)."""
        raise NotImplementedError()

    def turn_off(self, **kwargs: Any) -> None:
        """Switch off the output (sync wrapper)."""
        raise NotImplementedError()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch on the output."""
        if self._pin is None:
            _LOGGER.error("Pin needed to switch ON the output")
            return

        await self._coordinator.client.switch_output(self._idx, self._pin, True)
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch off the output."""
        if self._pin is None:
            _LOGGER.error("Pin needed to switch OFF the output")
            return
        await self._coordinator.client.switch_output(self._idx, self._pin, False)
        await self._coordinator.async_refresh()
