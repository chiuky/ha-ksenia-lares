"""An implementation of a Lares alarm control panel."""

import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelState,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_PARTITION_AWAY,
    CONF_PARTITION_HOME,
    CONF_PARTITION_NIGHT,
    CONF_SCENARIO_AWAY,
    CONF_SCENARIO_DISARM,
    CONF_SCENARIO_HOME,
    CONF_SCENARIO_NIGHT,
    DATA_PARTITIONS,
    DOMAIN,
    PARTITION_STATUS_ARMED,
    PARTITION_STATUS_ARMED_IMMEDIATE,
    PARTITION_STATUS_ARMING,
)
from .coordinator import LaresDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class LaresAlarmControlPanelEntity(CoordinatorEntity, AlarmControlPanelEntity):
    """An implementation of a Lares alarm control panel."""

    TYPE = DOMAIN
    ARMED_STATUS = [PARTITION_STATUS_ARMED, PARTITION_STATUS_ARMED_IMMEDIATE]

    def __init__(
        self,
        coordinator: LaresDataUpdateCoordinator,
        device_info: dict,
        partition_descriptions: dict,
        scenario_descriptions: dict,
        options: dict,
    ) -> None:
        """Initialize a the switch."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._partition_descriptions = partition_descriptions
        self._scenario_descriptions = scenario_descriptions
        self._options = options
        self._attr_code_format = CodeFormat.NUMBER
        self._attr_device_info = device_info
        self._attr_code_arm_required = True
        self._attr_has_entity_name = True

        # Calculate supported features
        supported_features = AlarmControlPanelEntityFeature(0)
        if self._options[CONF_SCENARIO_AWAY] != "":
            supported_features |= AlarmControlPanelEntityFeature.ARM_AWAY
        if self._options[CONF_SCENARIO_HOME] != "":
            supported_features |= AlarmControlPanelEntityFeature.ARM_HOME
        if self._options[CONF_SCENARIO_NIGHT] != "":
            supported_features |= AlarmControlPanelEntityFeature.ARM_NIGHT
        self._attr_supported_features = supported_features

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this entity."""
        name = self._attr_device_info["name"].replace(" ", "_")
        return f"lares_control_panel_{name}"

    @property
    def name(self) -> str:
        """Return the name of this panel."""
        name = self._attr_device_info["name"]
        return f"Panel {name}"

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state of this panel."""
        if self.__has_partition_with_status([PARTITION_STATUS_ARMING]):
            return AlarmControlPanelState.ARMING

        if self.__is_armed(CONF_PARTITION_AWAY):
            return AlarmControlPanelState.ARMED_AWAY

        if self.__is_armed(CONF_PARTITION_HOME):
            return AlarmControlPanelState.ARMED_HOME

        if self.__is_armed(CONF_PARTITION_NIGHT):
            return AlarmControlPanelState.ARMED_NIGHT

        # If any of the not mapped partitions is armed, show custom as fallback
        if self.__has_partition_with_status(self.ARMED_STATUS):
            return AlarmControlPanelState.ARMED_CUSTOM_BYPASS

        return AlarmControlPanelState.DISARMED

    def alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command (sync wrapper)."""
        raise NotImplementedError()

    def alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command (sync wrapper)."""
        raise NotImplementedError()

    def alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command (sync wrapper)."""
        raise NotImplementedError()

    def alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command (sync wrapper)."""
        raise NotImplementedError()

    def alarm_arm_vacation(self, code: str | None = None) -> None:
        """Send arm vacation command (not supported)."""
        raise NotImplementedError()

    def alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        """Send arm custom bypass command (not supported)."""
        raise NotImplementedError()

    def alarm_trigger(self, code: str | None = None) -> None:
        """Send alarm trigger command (not supported)."""
        raise NotImplementedError()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self.__command(CONF_SCENARIO_DISARM, code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.__command(CONF_SCENARIO_HOME, code)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.__command(CONF_SCENARIO_AWAY, code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        await self.__command(CONF_SCENARIO_NIGHT, code)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        """Send arm vacation command (not supported)."""
        _LOGGER.warning("Arm vacation is not supported by Lares alarm")

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        """Send arm custom bypass command (not supported)."""
        _LOGGER.warning("Arm custom bypass is not supported by Lares alarm")

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        """Send alarm trigger command (not supported)."""
        _LOGGER.warning("Alarm trigger is not supported by Lares alarm")

    def __has_partition_with_status(self, status_list: list[str]) -> bool:
        """Return if any partitions is arming."""
        partitions = enumerate(self._coordinator.data[DATA_PARTITIONS])
        in_state = [
            idx for idx, partition in partitions if partition["status"] in status_list
        ]

        _LOGGER.debug("%s in status %s", in_state, status_list)

        return len(in_state) > 0

    def __is_armed(self, key: str) -> bool:
        """Return if all partitions linked to the configuration key are armed."""
        partition_names = self._options[key]

        # Skip the check if no partitions are linked
        if len(partition_names) == 0:
            _LOGGER.debug("Skipping %s armed check, no definition", key)
            return False

        descriptions = enumerate(self._partition_descriptions)
        to_check = (idx for idx, name in descriptions if name in partition_names)

        _LOGGER.debug("Checking %s (%s) for %s", partition_names, to_check, key)

        for idx in to_check:
            if (
                self._coordinator.data[DATA_PARTITIONS][idx]["status"]
                not in self.ARMED_STATUS
            ):
                return False

        return True

    async def __command(self, key: str, code: str | None = None) -> None:
        """Send arm home command."""
        scenario_name = self._options.get(key)

        if not scenario_name:
            _LOGGER.warning("Skipping command %s: no scenario configured", key)
            return

        if code is None:
            _LOGGER.warning("Skipping command %s: no PIN code provided", key)
            return

        descriptions = enumerate(self._scenario_descriptions)
        match_gen = (idx for idx, name in descriptions if name == scenario_name)
        matches = list(match_gen)

        if len(matches) != 1:
            _LOGGER.error(
                "Scenario configuration error for %s: found %d matches for '%s'",
                key,
                len(matches),
                scenario_name,
            )
            return

        scenario = matches[0]
        _LOGGER.info("Activating scenario %d (%s) for %s", scenario, scenario_name, key)

        try:
            result = await self._coordinator.client.activate_scenario(scenario, code)
            if result:
                _LOGGER.info("Successfully activated scenario %d", scenario)
                await self._coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to activate scenario %d", scenario)
        except Exception as err:
            _LOGGER.error("Error activating scenario %d: %s", scenario, err, exc_info=True)
