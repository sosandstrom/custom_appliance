"""DataUpdateCoordinator for custom_appliance."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .state_machine import CustomApplianceStateMachine

if TYPE_CHECKING:
    from .data import ApplianceConfig, CustomApplianceConfigEntry

_LOGGER = logging.getLogger(__name__)


class ApplianceDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from multiple appliances."""

    config_entry: CustomApplianceConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        appliances: dict[str, ApplianceConfig],
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
        )

        self._appliances = appliances
        self._state_machines: dict[str, CustomApplianceStateMachine] = {}
        self._unsubscribe_listeners: list[callable] = []

        # Initialize state machines for each appliance
        for appliance_id, config in appliances.items():
            self._state_machines[appliance_id] = CustomApplianceStateMachine(config)

        # Set up listeners for power sensor changes
        self._setup_power_sensor_listeners()

    def _setup_power_sensor_listeners(self) -> None:
        """Set up listeners for power sensor state changes."""
        # Get all unique power sensor entity IDs
        power_sensors = list(
            {config.power_sensor_entity_id for config in self._appliances.values()}
        )

        # Verify sensors exist
        for sensor_id in power_sensors:
            state = self.hass.states.get(sensor_id)
            if state is None:
                _LOGGER.warning("Power sensor %s not found", sensor_id)
                continue

            try:
                # Try to convert the state to float to validate it's a numeric sensor
                float(state.state)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Power sensor %s has non-numeric state: %s", sensor_id, state.state
                )

        # Set up the listener
        unsubscribe = async_track_state_change_event(
            self.hass,
            power_sensors,
            self._handle_power_sensor_change,
        )
        self._unsubscribe_listeners.append(unsubscribe)

    @callback
    def _handle_power_sensor_change(self, event: Event) -> None:
        """Handle power sensor state changes."""
        entity_id = event.data["entity_id"]
        new_state = event.data.get("new_state")

        if new_state is None:
            return

        try:
            power_value = float(new_state.state)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid power reading from %s: %s", entity_id, new_state.state
            )
            return

        # Update all appliances that use this power sensor
        state_changed = False
        for appliance_id, config in self._appliances.items():
            if config.power_sensor_entity_id == entity_id:
                state_machine = self._state_machines[appliance_id]
                if state_machine.update_power(power_value):
                    state_changed = True
                    _LOGGER.debug(
                        "Appliance %s state changed to %s (power: %.2fW)",
                        config.name,
                        state_machine.state_name,
                        power_value,
                    )

        # Trigger coordinator update if any state changed
        if state_changed:
            self.async_set_updated_data(self._get_coordinator_data())

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from appliances."""
        return self._get_coordinator_data()

    def _get_coordinator_data(self) -> dict[str, Any]:
        """Get current data from all state machines."""
        data = {}
        for appliance_id, state_machine in self._state_machines.items():
            data[appliance_id] = state_machine.get_state_data()
        return data

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        # Initial data load - get current power readings
        for appliance_id, config in self._appliances.items():
            power_sensor_state = self.hass.states.get(config.power_sensor_entity_id)
            if power_sensor_state is not None:
                try:
                    power_value = float(power_sensor_state.state)
                    self._state_machines[appliance_id].update_power(power_value)
                except (ValueError, TypeError):
                    _LOGGER.warning(
                        "Initial power reading for %s is invalid: %s",
                        config.name,
                        power_sensor_state.state,
                    )

        # Set initial data
        self.async_set_updated_data(self._get_coordinator_data())

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        # Clean up listeners
        for unsubscribe in self._unsubscribe_listeners:
            unsubscribe()
        self._unsubscribe_listeners.clear()

    def get_appliance_config(self, appliance_id: str) -> ApplianceConfig | None:
        """Get appliance configuration."""
        return self._appliances.get(appliance_id)

    def get_state_machine(
        self, appliance_id: str
    ) -> CustomApplianceStateMachine | None:
        """Get state machine for appliance."""
        return self._state_machines.get(appliance_id)

    def get_appliance_ids(self) -> list[str]:
        """Get list of all appliance IDs."""
        return list(self._appliances.keys())

    async def async_update_appliances(
        self, new_appliances: dict[str, ApplianceConfig]
    ) -> None:
        """Update appliances configuration."""
        # Clean up old listeners
        for unsubscribe in self._unsubscribe_listeners:
            unsubscribe()
        self._unsubscribe_listeners.clear()

        # Update appliances and state machines
        self._appliances = new_appliances

        # Remove state machines for deleted appliances
        current_ids = set(self._state_machines.keys())
        new_ids = set(new_appliances.keys())
        for removed_id in current_ids - new_ids:
            del self._state_machines[removed_id]

        # Add/update state machines for current appliances
        for appliance_id, config in new_appliances.items():
            if appliance_id in self._state_machines:
                # Update existing state machine config
                self._state_machines[appliance_id].config = config
            else:
                # Create new state machine
                self._state_machines[appliance_id] = CustomApplianceStateMachine(config)

        # Set up new listeners
        self._setup_power_sensor_listeners()

        # Update data
        await self.async_setup()
