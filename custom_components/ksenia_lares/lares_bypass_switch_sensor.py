"""Implement Lares zone bypass switch."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_PIN, DATA_ZONES, ZONE_BYPASS_ON, ZONE_STATUS_NOT_USED
from .coordinator import LaresDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class LaresBypassSwitchSensor(CoordinatorEntity, SwitchEntity):
    """Implement Lares zone bypass switch."""

    _attr_translation_key = "bypass"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:shield-off"

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

        self._attr_unique_id = f"lares_bypass_{self._idx}"
        self._attr_device_info = device_info
        self._attr_name = description

        is_used = (
            self._coordinator.data[DATA_ZONES][self._idx]["status"]
            != ZONE_STATUS_NOT_USED
        )

        self._attr_entity_registry_enabled_default = is_used
        self._attr_entity_registry_visible_default = is_used

    @property
    def is_on(self) -> bool | None:
        """Return true if the zone is bypassed."""
        status = self._coordinator.data[DATA_ZONES][self._idx]["bypass"]
        return status == ZONE_BYPASS_ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Bypass the zone."""
        if self._pin is None:
            _LOGGER.error("Pin needed for bypass zone")
            return

        await self._coordinator.client.bypass_zone(self._idx, self._pin, True)
        await self._coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unbypass the zone."""
        if self._pin is None:
            _LOGGER.error("Pin needed for unbypass zone")
            return

        await self._coordinator.client.bypass_zone(self._idx, self._pin, False)
        await self._coordinator.async_refresh()
