"""Config flow for Ksenia Lares Alarm integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .base import LaresBase
from .const import (
    CONF_PARTITION_AWAY,
    CONF_PARTITION_NIGHT,
    CONF_SCAN_INTERVAL_OUTPUTS,
    CONF_SCAN_INTERVAL_PARTITIONS,
    CONF_SCAN_INTERVAL_TEMPERATURES,
    CONF_SCAN_INTERVAL_ZONES,
    CONF_SCENARIO_AWAY,
    CONF_SCENARIO_DISARM,
    CONF_SCENARIO_NIGHT,
    CONF_ALARM_PANELS,
    CONF_ALARM_PANEL_NAME,
    CONF_ALARM_PANEL_PIN,
    DEFAULT_SCAN_INTERVAL_OUTPUTS,
    DEFAULT_SCAN_INTERVAL_PARTITIONS,
    DEFAULT_SCAN_INTERVAL_TEMPERATURES,
    DEFAULT_SCAN_INTERVAL_ZONES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Schema definitions
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("port", default=80): int,
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Optional("automation_pin"): str,
        vol.Required("scan_interval", default=10): int,
    }
)

STEP_SCAN_INTERVALS_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_SCAN_INTERVAL_ZONES,
            default=DEFAULT_SCAN_INTERVAL_ZONES,
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
        vol.Optional(
            CONF_SCAN_INTERVAL_PARTITIONS,
            default=DEFAULT_SCAN_INTERVAL_PARTITIONS,
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
        vol.Optional(
            CONF_SCAN_INTERVAL_TEMPERATURES,
            default=DEFAULT_SCAN_INTERVAL_TEMPERATURES,
        ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
        vol.Optional(
            CONF_SCAN_INTERVAL_OUTPUTS,
            default=DEFAULT_SCAN_INTERVAL_OUTPUTS,
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
    }
)


def build_panel_schema(
    partitions: list[str],
    scenarios: list[str],
    panel_name_default: str = "",
    panel_name_editable: bool = True,
    panel_data: dict | None = None,
) -> vol.Schema:
    """Build a dynamic schema for panel configuration."""
    # Sort partitions and scenarios alphabetically
    sorted_partitions = sorted(
        [v for v in list(filter(None, partitions)) if v != ""])
    sorted_scenarios = sorted(scenarios)

    select_partitions = {v: v for v in sorted_partitions}

    if panel_data is None:
        panel_data = {}

    fields = {}

    if panel_name_editable:
        fields[vol.Required(CONF_ALARM_PANEL_NAME,
                            default=panel_name_default)] = str
    else:
        # For edit: show panel name as fixed
        fields[vol.Required(
            CONF_ALARM_PANEL_NAME,
            default=panel_data.get(CONF_ALARM_PANEL_NAME, panel_name_default)
        )] = vol.In([panel_data.get(CONF_ALARM_PANEL_NAME)])

    if panel_name_editable or not panel_data:
        fields[vol.Required(CONF_ALARM_PANEL_PIN)] = str
    else:
        # For edit: PIN is optional
        fields[vol.Optional(CONF_ALARM_PANEL_PIN)] = str

    fields[vol.Required(
        CONF_SCENARIO_DISARM,
        default=panel_data.get(CONF_SCENARIO_DISARM, "")
    )] = vol.In(sorted_scenarios)

    fields[vol.Required(
        CONF_SCENARIO_AWAY,
        default=panel_data.get(CONF_SCENARIO_AWAY, "")
    )] = vol.In(sorted_scenarios)

    fields[vol.Optional(
        CONF_PARTITION_AWAY,
        default=panel_data.get(CONF_PARTITION_AWAY, [])
    )] = cv.multi_select(select_partitions)

    fields[vol.Optional(
        CONF_SCENARIO_NIGHT,
        default=panel_data.get(CONF_SCENARIO_NIGHT, "")
    )] = vol.In(["", *sorted_scenarios])

    fields[vol.Optional(
        CONF_PARTITION_NIGHT,
        default=panel_data.get(CONF_PARTITION_NIGHT, [])
    )] = cv.multi_select(select_partitions)

    return vol.Schema(fields)


def build_panels_management_schema(panels: list[dict]) -> vol.Schema:
    """Build schema for panels management step."""
    fields = {
        vol.Required("action", default="done"): vol.In(
            {"add": "Add", "edit": "Edit", "delete": "Delete", "done": "Finish"}
        )
    }

    if panels:
        fields[vol.Optional("panel_to_edit")] = vol.In(
            [p.get(CONF_ALARM_PANEL_NAME) for p in panels]
        )
    else:
        fields[vol.Optional("panel_to_edit")] = str

    if len(panels) > 1:
        fields[vol.Optional("panel_to_delete")] = vol.In(
            [p.get(CONF_ALARM_PANEL_NAME) for p in panels]
        )
    else:
        fields[vol.Optional("panel_to_delete")] = str

    return vol.Schema(fields)


def build_options_init_schema(
    zones_default: int,
    partitions_default: int,
    temperatures_default: int,
    outputs_default: int,
) -> vol.Schema:
    """Build schema for options flow init step."""
    return vol.Schema(
        {
            vol.Optional(
                CONF_SCAN_INTERVAL_ZONES,
                default=zones_default,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
            vol.Optional(
                CONF_SCAN_INTERVAL_PARTITIONS,
                default=partitions_default,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
            vol.Optional(
                CONF_SCAN_INTERVAL_TEMPERATURES,
                default=temperatures_default,
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
            vol.Optional(
                CONF_SCAN_INTERVAL_OUTPUTS,
                default=outputs_default,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
        }
    )


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    client = LaresBase(data)
    _ = hass  # mark hass as used to silence linter

    info = await client.info()

    if info is None:
        raise InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": info["name"], "id": info["id"]}


class LaresConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ksenia Lares Alarm."""

    VERSION = 4

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_data: dict[str, Any] = {}
        self._scan_options: dict[str, Any] = {}
        self._panels: list[dict[str, Any]] = []
        self._client: LaresBase | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Return the options flow."""
        return LaresOptionsFlowHandler(config_entry)

    def is_matching(self, other_flow: str) -> bool:
        """Satisfy abstract interface signature."""
        return other_flow == DOMAIN

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial step: connection credentials."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Abort in case the host was already configured before.
            await self.async_set_unique_id(str(info["id"]))
            self._abort_if_unique_id_configured()

            # Save connection data, proceed to scan intervals
            self._user_data = user_input
            self._client = LaresBase(user_input)
            return await self.async_step_scan_intervals()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_scan_intervals(self, user_input=None) -> ConfigFlowResult:
        """Configure scan intervals for different resources."""
        if user_input is not None:
            self._scan_options = user_input
            # Proceed to configure the first panel (mandatory)
            return await self.async_step_first_panel()

        return self.async_show_form(step_id="scan_intervals", data_schema=STEP_SCAN_INTERVALS_SCHEMA)

    async def async_step_first_panel(self, user_input=None) -> ConfigFlowResult:
        """Configure the first alarm panel (mandatory)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input.get(CONF_ALARM_PANEL_NAME)
            pin = user_input.get(CONF_ALARM_PANEL_PIN)

            panel_def = {
                CONF_ALARM_PANEL_NAME: name,
                CONF_ALARM_PANEL_PIN: pin,
                CONF_PARTITION_AWAY: user_input.get(CONF_PARTITION_AWAY, []),
                CONF_PARTITION_NIGHT: user_input.get(CONF_PARTITION_NIGHT, []),
                CONF_SCENARIO_DISARM: user_input.get(CONF_SCENARIO_DISARM, ""),
                CONF_SCENARIO_AWAY: user_input.get(CONF_SCENARIO_AWAY, ""),
                CONF_SCENARIO_NIGHT: user_input.get(CONF_SCENARIO_NIGHT, ""),
            }
            self._panels.append(panel_def)
            # Proceed to panel management (add more or finish)
            return await self.async_step_panels()

        partitions = await self._client.partition_descriptions()
        scenarios = await self._client.scenario_descriptions()

        return self.async_show_form(
            step_id="first_panel",
            data_schema=build_panel_schema(
                partitions, scenarios, panel_name_default="Alarm panel"
            ),
            errors=errors,
        )

    async def async_step_panels(self, user_input=None) -> ConfigFlowResult:
        """Manage alarm panels: add more, edit, delete, or finish."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "add":
                return await self.async_step_add_panel()
            if action == "edit":
                panel_name = user_input.get("panel_to_edit")
                if panel_name:
                    return await self.async_step_edit_panel({"target": panel_name})
            if action == "delete":
                panel_name = user_input.get("panel_to_delete")
                if panel_name and len(self._panels) > 1:
                    self._panels = [
                        p
                        for p in self._panels
                        if p.get(CONF_ALARM_PANEL_NAME) != panel_name
                    ]
                    return await self.async_step_panels()
            if action == "done":
                # Save all configuration
                data = {**self._user_data, **self._scan_options}
                options = {CONF_ALARM_PANELS: self._panels}
                return self.async_create_entry(
                    title=self._user_data.get("host", "Lares Alarm"),
                    data=data,
                    options=options,
                )

        panel_list = (
            "\n".join(
                f"- {p.get(CONF_ALARM_PANEL_NAME)}" for p in self._panels)
            or "No panels configured"
        )

        return self.async_show_form(
            step_id="panels",
            data_schema=build_panels_management_schema(self._panels),
            description_placeholders={"panel_list": panel_list},
        )

    async def async_step_add_panel(self, user_input=None) -> ConfigFlowResult:
        """Add a new alarm panel."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input.get(CONF_ALARM_PANEL_NAME)
            pin = user_input.get(CONF_ALARM_PANEL_PIN)

            if any(p.get(CONF_ALARM_PANEL_NAME) == name for p in self._panels):
                errors[CONF_ALARM_PANEL_NAME] = "name_exists"
            else:
                panel_def = {
                    CONF_ALARM_PANEL_NAME: name,
                    CONF_ALARM_PANEL_PIN: pin,
                    CONF_PARTITION_AWAY: user_input.get(CONF_PARTITION_AWAY, []),
                    CONF_PARTITION_NIGHT: user_input.get(CONF_PARTITION_NIGHT, []),
                    CONF_SCENARIO_DISARM: user_input.get(CONF_SCENARIO_DISARM, ""),
                    CONF_SCENARIO_AWAY: user_input.get(CONF_SCENARIO_AWAY, ""),
                    CONF_SCENARIO_NIGHT: user_input.get(CONF_SCENARIO_NIGHT, ""),
                }
                self._panels.append(panel_def)
                return await self.async_step_panels()

        partitions = await self._client.partition_descriptions()
        scenarios = await self._client.scenario_descriptions()

        return self.async_show_form(
            step_id="add_panel",
            data_schema=build_panel_schema(partitions, scenarios),
            errors=errors,
        )

    async def async_step_edit_panel(self, user_input=None) -> ConfigFlowResult:
        """Edit an existing alarm panel."""
        errors: dict[str, str] = {}

        target_name = None
        if user_input and "target" in user_input and not user_input.get(
            CONF_ALARM_PANEL_NAME
        ):
            target_name = user_input["target"]
        elif user_input and CONF_ALARM_PANEL_NAME in user_input:
            target_name = user_input.get(CONF_ALARM_PANEL_NAME)

        panel = next(
            (
                p
                for p in self._panels
                if p.get(CONF_ALARM_PANEL_NAME) == target_name
            ),
            None,
        )
        if panel is None:
            return await self.async_step_panels()

        if user_input and "target" not in user_input:
            # Save edits
            new_pin = user_input.get(CONF_ALARM_PANEL_PIN)
            if new_pin:
                panel[CONF_ALARM_PANEL_PIN] = new_pin
            panel[CONF_SCENARIO_DISARM] = user_input.get(
                CONF_SCENARIO_DISARM, panel.get(CONF_SCENARIO_DISARM, "")
            )
            panel[CONF_SCENARIO_AWAY] = user_input.get(
                CONF_SCENARIO_AWAY, panel.get(CONF_SCENARIO_AWAY, "")
            )
            panel[CONF_SCENARIO_NIGHT] = user_input.get(
                CONF_SCENARIO_NIGHT, panel.get(CONF_SCENARIO_NIGHT, "")
            )
            panel[CONF_PARTITION_AWAY] = user_input.get(
                CONF_PARTITION_AWAY, panel.get(CONF_PARTITION_AWAY, [])
            )
            panel[CONF_PARTITION_NIGHT] = user_input.get(
                CONF_PARTITION_NIGHT, panel.get(CONF_PARTITION_NIGHT, [])
            )
            return await self.async_step_panels()

        partitions = await self._client.partition_descriptions()
        scenarios = await self._client.scenario_descriptions()

        return self.async_show_form(
            step_id="edit_panel",
            data_schema=build_panel_schema(
                partitions, scenarios, panel_name_editable=False, panel_data=panel
            ),
            errors=errors,
            description_placeholders={
                "panel_name": panel.get(CONF_ALARM_PANEL_NAME)
            },
        )


class LaresOptionsFlowHandler(OptionsFlow):
    """Handle options flow for Ksenia Lares Alarm."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.client = LaresBase(config_entry.data)
        self._base_options: dict[str, Any] = {}
        self._panels: list[dict[str, Any]] = []

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        """Manage scan interval options."""
        if user_input is not None:
            self._base_options = user_input
            # Load existing panels
            self._panels = list(
                self.config_entry.options.get(CONF_ALARM_PANELS, []))
            return await self.async_step_panels()

        zones_default = self.config_entry.options.get(
            CONF_SCAN_INTERVAL_ZONES,
            self.config_entry.data.get(
                CONF_SCAN_INTERVAL_ZONES, DEFAULT_SCAN_INTERVAL_ZONES
            ),
        )
        partitions_default = self.config_entry.options.get(
            CONF_SCAN_INTERVAL_PARTITIONS,
            self.config_entry.data.get(
                CONF_SCAN_INTERVAL_PARTITIONS,
                DEFAULT_SCAN_INTERVAL_PARTITIONS,
            ),
        )
        temperatures_default = self.config_entry.options.get(
            CONF_SCAN_INTERVAL_TEMPERATURES,
            self.config_entry.data.get(
                CONF_SCAN_INTERVAL_TEMPERATURES,
                DEFAULT_SCAN_INTERVAL_TEMPERATURES,
            ),
        )
        outputs_default = self.config_entry.options.get(
            CONF_SCAN_INTERVAL_OUTPUTS,
            self.config_entry.data.get(
                CONF_SCAN_INTERVAL_OUTPUTS, DEFAULT_SCAN_INTERVAL_OUTPUTS
            ),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=build_options_init_schema(
                zones_default, partitions_default, temperatures_default, outputs_default
            ),
        )

    async def async_step_panels(self, user_input=None) -> ConfigFlowResult:
        """Manage alarm panels (add/edit/delete)."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "add":
                return await self.async_step_add_panel()
            if action == "edit":
                panel_name = user_input.get("panel_to_edit")
                if panel_name:
                    return await self.async_step_edit_panel({"target": panel_name})
            if action == "delete":
                panel_name = user_input.get("panel_to_delete")
                if panel_name and len(self._panels) > 1:
                    self._panels = [
                        p
                        for p in self._panels
                        if p.get(CONF_ALARM_PANEL_NAME) != panel_name
                    ]
                    return await self.async_step_panels()
            if action == "done":
                combined = {**self._base_options,
                            CONF_ALARM_PANELS: self._panels}
                return self.async_create_entry(title="", data=combined)

        panel_list = (
            "\n".join(
                f"- {p.get(CONF_ALARM_PANEL_NAME)}" for p in self._panels)
            or "No panels configured"
        )

        return self.async_show_form(
            step_id="panels",
            data_schema=build_panels_management_schema(self._panels),
            description_placeholders={"panel_list": panel_list},
        )

    async def async_step_add_panel(self, user_input=None) -> ConfigFlowResult:
        """Add a new alarm panel."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input.get(CONF_ALARM_PANEL_NAME)
            pin = user_input.get(CONF_ALARM_PANEL_PIN)

            if any(p.get(CONF_ALARM_PANEL_NAME) == name for p in self._panels):
                errors[CONF_ALARM_PANEL_NAME] = "name_exists"
            else:
                panel_def = {
                    CONF_ALARM_PANEL_NAME: name,
                    CONF_ALARM_PANEL_PIN: pin,
                    CONF_PARTITION_AWAY: user_input.get(CONF_PARTITION_AWAY, []),
                    CONF_PARTITION_NIGHT: user_input.get(CONF_PARTITION_NIGHT, []),
                    CONF_SCENARIO_DISARM: user_input.get(CONF_SCENARIO_DISARM, ""),
                    CONF_SCENARIO_AWAY: user_input.get(CONF_SCENARIO_AWAY, ""),
                    CONF_SCENARIO_NIGHT: user_input.get(CONF_SCENARIO_NIGHT, ""),
                }
                self._panels.append(panel_def)
                return await self.async_step_panels()

        partitions = await self.client.partition_descriptions()
        scenarios = await self.client.scenario_descriptions()

        return self.async_show_form(
            step_id="add_panel",
            data_schema=build_panel_schema(partitions, scenarios),
            errors=errors,
            description_placeholders={
                "info": "Configure a dedicated alarm panel"
            },
        )

    async def async_step_edit_panel(self, user_input=None) -> ConfigFlowResult:
        """Edit an existing alarm panel."""
        errors: dict[str, str] = {}

        target_name = None
        if user_input and "target" in user_input and not user_input.get(
            CONF_ALARM_PANEL_NAME
        ):
            target_name = user_input["target"]
        elif user_input and CONF_ALARM_PANEL_NAME in user_input:
            target_name = user_input.get(CONF_ALARM_PANEL_NAME)

        panel = next(
            (
                p
                for p in self._panels
                if p.get(CONF_ALARM_PANEL_NAME) == target_name
            ),
            None,
        )
        if panel is None:
            return await self.async_step_panels()

        if user_input and "target" not in user_input:
            # Save edits
            new_pin = user_input.get(CONF_ALARM_PANEL_PIN)
            if new_pin:
                panel[CONF_ALARM_PANEL_PIN] = new_pin
            panel[CONF_SCENARIO_DISARM] = user_input.get(
                CONF_SCENARIO_DISARM, panel.get(CONF_SCENARIO_DISARM, "")
            )
            panel[CONF_SCENARIO_AWAY] = user_input.get(
                CONF_SCENARIO_AWAY, panel.get(CONF_SCENARIO_AWAY, "")
            )
            panel[CONF_SCENARIO_NIGHT] = user_input.get(
                CONF_SCENARIO_NIGHT, panel.get(CONF_SCENARIO_NIGHT, "")
            )
            panel[CONF_PARTITION_AWAY] = user_input.get(
                CONF_PARTITION_AWAY, panel.get(CONF_PARTITION_AWAY, [])
            )
            panel[CONF_PARTITION_NIGHT] = user_input.get(
                CONF_PARTITION_NIGHT, panel.get(CONF_PARTITION_NIGHT, [])
            )
            return await self.async_step_panels()

        partitions = await self.client.partition_descriptions()
        scenarios = await self.client.scenario_descriptions()

        return self.async_show_form(
            step_id="edit_panel",
            data_schema=build_panel_schema(
                partitions, scenarios, panel_name_editable=False, panel_data=panel
            ),
            errors=errors,
            description_placeholders={
                "info": f"Edit alarm panel '{panel.get(CONF_ALARM_PANEL_NAME)}' (PIN optional)"
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
