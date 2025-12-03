"""An implementation of a Lares alarm control panel."""

import logging
from typing import ClassVar

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
    CONF_PARTITION_NIGHT,
    CONF_SCENARIO_AWAY,
    CONF_SCENARIO_DISARM,
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

    TYPE: ClassVar[str] = DOMAIN
    ARMED_STATUS: ClassVar[list[str]] = [
        PARTITION_STATUS_ARMED,
        PARTITION_STATUS_ARMED_IMMEDIATE,
    ]

    def __init__(
        self,
        coordinator: LaresDataUpdateCoordinator,
        device_info: dict,
        partition_descriptions: list[str],
        scenario_descriptions: list[str],
        panel_config: dict,
    ) -> None:
        """Initialize the alarm control panel entity for a given panel configuration."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._partition_descriptions = partition_descriptions
        self._scenario_descriptions = scenario_descriptions
        self._panel = panel_config
        # Keep backward compatibility with existing option key usage
        self._options = panel_config
        self._attr_code_format = CodeFormat.NUMBER
        self._attr_device_info = device_info
        # If panel has its own PIN we can auto arm without user entry
        self._panel_pin = panel_config.get("panel_pin") or panel_config.get("pin")
        self._attr_code_arm_required = not bool(self._panel_pin)
        self._attr_has_entity_name = True

        # Calculate supported features
        supported_features = AlarmControlPanelEntityFeature(0)
        if self._options[CONF_SCENARIO_AWAY] != "":
            supported_features |= AlarmControlPanelEntityFeature.ARM_AWAY
        if self._options[CONF_SCENARIO_NIGHT] != "":
            supported_features |= AlarmControlPanelEntityFeature.ARM_NIGHT
        self._attr_supported_features = supported_features

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this entity."""
        base_name = self._attr_device_info["name"].replace(" ", "_")
        panel_name = self._panel.get("panel_name", "default").replace(" ", "_").lower()
        return f"lares_control_panel_{base_name}_{panel_name}"

    @property
    def name(self) -> str:
        """Return the name of this panel."""
        device_name = self._attr_device_info["name"]
        panel_name = self._panel.get("panel_name", "Default")
        return f"{panel_name} ({device_name})"

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state of this panel."""
        if self.__has_partition_with_status([PARTITION_STATUS_ARMING]):
            return AlarmControlPanelState.ARMING

        if self.__is_armed(CONF_PARTITION_AWAY):
            return AlarmControlPanelState.ARMED_AWAY

        if self.__is_armed(CONF_PARTITION_NIGHT):
            return AlarmControlPanelState.ARMED_NIGHT

        # If any of the not mapped partitions is armed, show custom as fallback
        if self.__has_partition_with_status(self.ARMED_STATUS):
            return AlarmControlPanelState.ARMED_CUSTOM_BYPASS

        return AlarmControlPanelState.DISARMED

    def alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command (sync wrapper)."""
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

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.__command(CONF_SCENARIO_AWAY, code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        await self.__command(CONF_SCENARIO_NIGHT, code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command (not supported)."""
        _LOGGER.warning("Arm home is not supported by Lares alarm")

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
        """Return if any of this panel's partitions has a status in the list.

        Previously this checked all partitions globally, which caused incorrect
        states when multiple panels existed on the same device. We now filter
        to only the partitions configured for this panel (away + night).
        """
        # Collect the partition names configured for this panel
        panel_partition_names = set(self._options.get(CONF_PARTITION_AWAY, []))
        panel_partition_names.update(self._options.get(CONF_PARTITION_NIGHT, []))

        if not panel_partition_names:
            _LOGGER.debug(
                "Panel %s has no configured partitions; skipping status check",
                self._panel.get("panel_name"),
            )
            return False

        # Map configured names to indices in descriptions
        name_to_index = {
            name: idx for idx, name in enumerate(self._partition_descriptions)
        }
        indices = [
            name_to_index[name]
            for name in panel_partition_names
            if name in name_to_index
        ]

        if not indices:
            _LOGGER.debug(
                "Panel %s configured partitions not found in descriptions: %s",
                self._panel.get("panel_name"),
                panel_partition_names,
            )
            return False

        # Check only the panel-specific partitions for the given statuses
        in_state = [
            idx
            for idx in indices
            if self._coordinator.data[DATA_PARTITIONS][idx]["status"] in status_list
        ]

        _LOGGER.debug(
            "Panel %s partitions in statuses %s: %s",
            self._panel.get("panel_name"),
            status_list,
            in_state,
        )

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
        """Execute scenario command for a given key using panel-specific configuration."""
        scenario_name = self._options.get(key)

        if not scenario_name:
            _LOGGER.debug(
                "Panel %s - scenario key %s not configured",
                self._panel.get("panel_name"),
                key,
            )
            return

        # Prefer panel configured PIN if available
        pin_code = self._panel_pin or code
        if not pin_code:
            _LOGGER.warning(
                "Panel %s - no PIN code available for command %s",
                self._panel.get("panel_name"),
                key,
            )
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
        _LOGGER.info(
            "Panel %s activating scenario %d (%s) for %s",
            self._panel.get("panel_name"),
            scenario,
            scenario_name,
            key,
        )

        try:
            result = await self._coordinator.client.activate_scenario(
                scenario, pin_code
            )
            if result:
                _LOGGER.info(
                    "Panel %s : scenario %d activated",
                    self._panel.get("panel_name"),
                    scenario,
                )
                await self._coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to activate scenario %d", scenario)
        except (OSError, TimeoutError, ConnectionError) as err:
            _LOGGER.error("Network error activating scenario %d: %s", scenario, err)
        except (KeyError, AttributeError) as err:
            _LOGGER.error("Invalid response activating scenario %d: %s", scenario, err)
        except RuntimeError as err:
            _LOGGER.error("Runtime error activating scenario %d: %s", scenario, err)
