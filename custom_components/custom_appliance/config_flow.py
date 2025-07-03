"""Config flow for Custom Appliance."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import area_registry as ar, entity_registry as er, selector

from .const import DOMAIN


class CustomApplianceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Custom Appliance."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Create the config entry with the first appliance
            appliance_id = user_input["name"].lower().replace(" ", "_")
            appliances = {
                appliance_id: {
                    "name": user_input["name"],
                    "power_sensor_entity_id": user_input["power_sensor"],
                    "area_id": user_input.get("area"),
                    "off_threshold": user_input["off_threshold"],
                    "running_threshold": user_input["running_threshold"],
                    "debounce_time": user_input["debounce_time"],
                    "complete_timeout": user_input["complete_timeout"],
                }
            }

            return self.async_create_entry(
                title="Custom Appliances",
                data={"appliances": appliances},
            )

        # Get available power sensors
        entity_registry = er.async_get(self.hass)
        power_sensors = [
            entity.entity_id
            for entity in entity_registry.entities.values()
            if entity.entity_id.startswith("sensor.")
            and (
                "power" in entity.entity_id.lower()
                or "watt" in entity.entity_id.lower()
            )
        ]

        # Get available areas
        area_registry = ar.async_get(self.hass)
        areas = [
            {"value": area.id, "label": area.name}
            for area in area_registry.areas.values()
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="My Appliance"): str,
                    vol.Required("power_sensor"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=power_sensors,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("area"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=areas,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required("off_threshold", default=5.0): vol.All(
                        vol.Coerce(float), vol.Range(min=0.0, max=100.0)
                    ),
                    vol.Required("running_threshold", default=50.0): vol.All(
                        vol.Coerce(float), vol.Range(min=1.0, max=5000.0)
                    ),
                    vol.Required("debounce_time", default=60): vol.All(
                        vol.Coerce(int), vol.Range(min=10, max=600)
                    ),
                    vol.Required("complete_timeout", default=300): vol.All(
                        vol.Coerce(int), vol.Range(min=60, max=3600)
                    ),
                }
            ),
            description_placeholders={
                "power_sensors_count": str(len(power_sensors)),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Custom Appliance."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._appliances: dict[str, dict] = config_entry.data.get("appliances", {})

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage appliances."""
        if user_input is not None:
            if user_input["action"] == "add":
                return await self.async_step_add_appliance()
            if user_input["action"] == "edit":
                return await self.async_step_select_appliance()
            if user_input["action"] == "delete":
                return await self.async_step_delete_appliance()

        appliances_list = [
            f"{config['name']} ({config['power_sensor_entity_id']})"
            for config in self._appliances.values()
        ]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("action"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": "add", "label": "Add new appliance"},
                                {"value": "edit", "label": "Edit existing appliance"},
                                {"value": "delete", "label": "Delete appliance"},
                            ],
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            description_placeholders={
                "appliances": "\\n".join(appliances_list)
                if appliances_list
                else "No appliances configured",
            },
        )

    async def async_step_add_appliance(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new appliance."""
        if user_input is not None:
            appliance_id = user_input["name"].lower().replace(" ", "_")
            if appliance_id in self._appliances:
                return self.async_show_form(
                    step_id="add_appliance",
                    data_schema=self._get_appliance_schema(user_input),
                    errors={"name": "name_exists"},
                )

            self._appliances[appliance_id] = {
                "name": user_input["name"],
                "power_sensor_entity_id": user_input["power_sensor"],
                "area_id": user_input.get("area"),
                "off_threshold": user_input["off_threshold"],
                "running_threshold": user_input["running_threshold"],
                "debounce_time": user_input["debounce_time"],
                "complete_timeout": user_input["complete_timeout"],
            }

            return self.async_create_entry(
                title="",
                data={"appliances": self._appliances},
            )

        return self.async_show_form(
            step_id="add_appliance",
            data_schema=self._get_appliance_schema(),
        )

    async def async_step_select_appliance(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select appliance to edit."""
        if user_input is not None:
            self._selected_appliance_id = user_input["appliance"]
            return await self.async_step_edit_appliance()

        appliance_options = [
            {"value": app_id, "label": config["name"]}
            for app_id, config in self._appliances.items()
        ]

        return self.async_show_form(
            step_id="select_appliance",
            data_schema=vol.Schema(
                {
                    vol.Required("appliance"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=appliance_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_edit_appliance(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit an existing appliance."""
        if user_input is not None:
            self._appliances[self._selected_appliance_id] = {
                "name": user_input["name"],
                "power_sensor_entity_id": user_input["power_sensor"],
                "area_id": user_input.get("area"),
                "off_threshold": user_input["off_threshold"],
                "running_threshold": user_input["running_threshold"],
                "debounce_time": user_input["debounce_time"],
                "complete_timeout": user_input["complete_timeout"],
            }

            return self.async_create_entry(
                title="",
                data={"appliances": self._appliances},
            )

        current_config = self._appliances[self._selected_appliance_id]
        return self.async_show_form(
            step_id="edit_appliance",
            data_schema=self._get_appliance_schema(
                {
                    "name": current_config["name"],
                    "power_sensor": current_config["power_sensor_entity_id"],
                    "area": current_config["area_id"],
                    "off_threshold": current_config["off_threshold"],
                    "running_threshold": current_config["running_threshold"],
                    "debounce_time": current_config["debounce_time"],
                    "complete_timeout": current_config["complete_timeout"],
                }
            ),
        )

    async def async_step_delete_appliance(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Delete an appliance."""
        if user_input is not None:
            del self._appliances[user_input["appliance"]]
            return self.async_create_entry(
                title="",
                data={"appliances": self._appliances},
            )

        appliance_options = [
            {"value": app_id, "label": config["name"]}
            for app_id, config in self._appliances.items()
        ]

        return self.async_show_form(
            step_id="delete_appliance",
            data_schema=vol.Schema(
                {
                    vol.Required("appliance"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=appliance_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    def _get_appliance_schema(
        self, defaults: dict[str, Any] | None = None
    ) -> vol.Schema:
        """Get schema for appliance configuration."""
        if defaults is None:
            defaults = {}

        # Get available power sensors
        entity_registry = er.async_get(self.hass)
        power_sensors = [
            entity.entity_id
            for entity in entity_registry.entities.values()
            if entity.entity_id.startswith("sensor.")
            and (
                "power" in entity.entity_id.lower()
                or "watt" in entity.entity_id.lower()
            )
        ]

        # Get available areas
        area_registry = ar.async_get(self.hass)
        areas = [
            {"value": area.id, "label": area.name}
            for area in area_registry.areas.values()
        ]

        return vol.Schema(
            {
                vol.Required("name", default=defaults.get("name", "My Appliance")): str,
                vol.Required(
                    "power_sensor", default=defaults.get("power_sensor")
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=power_sensors,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    "area", default=defaults.get("area")
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=areas,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "off_threshold", default=defaults.get("off_threshold", 5.0)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=100.0)),
                vol.Required(
                    "running_threshold", default=defaults.get("running_threshold", 50.0)
                ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=5000.0)),
                vol.Required(
                    "debounce_time", default=defaults.get("debounce_time", 60)
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=600)),
                vol.Required(
                    "complete_timeout", default=defaults.get("complete_timeout", 300)
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
            }
        )
