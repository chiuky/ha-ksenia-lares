"""Provide support for Lares zone bypass."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_PIN,
    DATA_COORDINATOR,
    DATA_OUTPUTS,
    DATA_ZONES,
    DOMAIN,
    OUTPUT_STATUS_ON,
    ZONE_BYPASS_ON,
    ZONE_STATUS_NOT_USED,
)
from .coordinator import LaresDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up zone bypass switches for zones in the Lares alarm device from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    device_info = await coordinator.client.device_info()
    zone_descriptions = await coordinator.client.zone_descriptions()
    output_descriptions = await coordinator.client.output_descriptions()
    options = {CONF_PIN: config_entry.options.get(CONF_PIN)}

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    zones = coordinator.data[DATA_ZONES]
    outputs = coordinator.data[DATA_OUTPUTS]

    def _async_add_laresBypassSwitch() -> None:
        entities = []
        zoneSensors = filterZoneSensors(
            coordinator, zones, zone_descriptions, device_info
        )
        outputSensors = filterOutputSensors(
            coordinator, outputs, output_descriptions, device_info
        )
        entities.extend(zoneSensors)
        entities.extend(outputSensors)
        async_add_entities(entities)

    def filterZoneSensors(coordinator, zones, zone_descriptions, device_info):
        entities = []
        for idx, zone in enumerate(zones):
            if zone is not None and zone["status"] != ZONE_STATUS_NOT_USED:
                entities.append(
                    LaresBypassSwitchSensor(
                        coordinator, idx, zone_descriptions[idx], device_info, options
                    )
                )
        return entities

    def filterOutputSensors(coordinator, outputs, output_descriptions, device_info):
        entities = []
        for idx, output in enumerate(outputs):
            if output is not None and output["type"] != ZONE_STATUS_NOT_USED:
                entities.append(
                    LaresOutputSensor(
                        coordinator, idx, output_descriptions[idx], device_info, options
                    )
                )
        return entities

    _async_add_laresBypassSwitch()


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

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unbypass the zone."""
        if self._pin is None:
            _LOGGER.error("Pin needed for unbypass zone")
            return

        await self._coordinator.client.bypass_zone(self._idx, self._pin, False)


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

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch on the output."""
        if self._pin is None:
            _LOGGER.error("Pin needed to switch ON the output")
            return

        await self._coordinator.client.switch_output(self._idx, self._pin, True)
        await self._coordinator.async_refresh()
        # await self._coordinator.client.outputs()  # refresh status
        # self.get_status()  # update icon

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch off the output."""
        if self._pin is None:
            _LOGGER.error("Pin needed to switch OFF the output")
            return
        await self._coordinator.client.switch_output(self._idx, self._pin, False)
        await self._coordinator.async_refresh()
        # await self._coordinator.client.outputs()  # refresh status
        # self.get_status()  # update icon
