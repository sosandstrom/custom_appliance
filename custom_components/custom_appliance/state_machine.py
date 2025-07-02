"""State machine for custom appliance power-based state detection."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .data import ApplianceConfig

_LOGGER = logging.getLogger(__name__)


class ApplianceState(Enum):
    """Appliance states based on power consumption."""

    OFF = "off"
    IDLE = "idle"
    RUNNING = "running"
    COMPLETE = "complete"


class CustomApplianceStateMachine:
    """State machine for custom appliance based on power consumption patterns."""

    def __init__(self, config: ApplianceConfig) -> None:
        """Initialize the state machine."""
        self.config = config
        self.current_state = ApplianceState.OFF
        self.last_state_change = datetime.now()
        self.last_power_reading = 0.0
        self.last_power_update = datetime.now()
        self.state_entry_time = datetime.now()
        self._previous_state = ApplianceState.OFF

    def update_power(self, power: float) -> bool:
        """
        Update power reading and potentially transition state.

        Returns True if state changed, False otherwise.
        """
        if power < 0:
            _LOGGER.warning(
                "Negative power reading %.2fW for appliance %s, ignoring",
                power,
                self.config.name,
            )
            return False

        self.last_power_reading = power
        self.last_power_update = datetime.now()

        new_state = self._determine_state_from_power(power)
        return self._transition_to_state(new_state)

    def _determine_state_from_power(self, power: float) -> ApplianceState:
        """Determine what state the appliance should be in based on power."""
        if power <= self.config.off_threshold:
            return ApplianceState.OFF
        if power >= self.config.running_threshold:
            return ApplianceState.RUNNING
        # Power is between off and running thresholds
        # If we were running and now in this range, check for completion
        if (
            self.current_state == ApplianceState.RUNNING
            and self._time_in_current_state()
            >= timedelta(seconds=self.config.debounce_time)
        ):
            return ApplianceState.COMPLETE
        if self.current_state == ApplianceState.COMPLETE:
            # Stay in complete state for the timeout period
            if self._time_in_current_state() >= timedelta(
                seconds=self.config.complete_timeout
            ):
                return ApplianceState.IDLE
            return ApplianceState.COMPLETE
        return ApplianceState.IDLE

    def _transition_to_state(self, new_state: ApplianceState) -> bool:
        """Transition to new state if conditions are met."""
        if new_state == self.current_state:
            return False

        # Check debounce time for state transitions
        time_in_state = self._time_in_current_state()
        if time_in_state < timedelta(seconds=self.config.debounce_time):
            # Not enough time in current state, don't transition yet
            # Exception: immediate transition to RUNNING (appliance turned on)
            if new_state != ApplianceState.RUNNING:
                return False

        # Special case: RUNNING to COMPLETE transition
        if (
            self.current_state == ApplianceState.RUNNING
            and new_state == ApplianceState.COMPLETE
        ):
            # Allow immediate transition to COMPLETE when power drops from RUNNING
            pass

        # Perform the transition
        self._previous_state = self.current_state
        self.current_state = new_state
        self.last_state_change = datetime.now()
        self.state_entry_time = datetime.now()

        _LOGGER.info(
            "Appliance %s transitioned from %s to %s (power: %.2fW)",
            self.config.name,
            self._previous_state.value,
            self.current_state.value,
            self.last_power_reading,
        )

        return True

    def _time_in_current_state(self) -> timedelta:
        """Get time spent in current state."""
        return datetime.now() - self.state_entry_time

    @property
    def is_running(self) -> bool:
        """Return True if appliance is currently running."""
        return self.current_state == ApplianceState.RUNNING

    @property
    def is_complete(self) -> bool:
        """Return True if appliance has completed a cycle."""
        return self.current_state == ApplianceState.COMPLETE

    @property
    def is_off(self) -> bool:
        """Return True if appliance is off."""
        return self.current_state == ApplianceState.OFF

    @property
    def is_idle(self) -> bool:
        """Return True if appliance is idle."""
        return self.current_state == ApplianceState.IDLE

    @property
    def state_name(self) -> str:
        """Return current state as string."""
        return self.current_state.value

    @property
    def time_in_state_seconds(self) -> int:
        """Return time in current state in seconds."""
        return int(self._time_in_current_state().total_seconds())

    @property
    def power_consumption(self) -> float:
        """Return current power consumption."""
        return self.last_power_reading

    def get_state_data(self) -> dict[str, any]:
        """Return state machine data for entities."""
        return {
            "state": self.state_name,
            "power": self.power_consumption,
            "time_in_state": self.time_in_state_seconds,
            "is_running": self.is_running,
            "is_complete": self.is_complete,
            "is_off": self.is_off,
            "is_idle": self.is_idle,
            "last_state_change": self.last_state_change.isoformat(),
            "last_power_update": self.last_power_update.isoformat(),
        }
