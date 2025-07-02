"""
Custom integration for power-based appliance state detection.

For more details about this integration, please refer to
https://github.com/sosandstrom/custom_appliance
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.loader import async_get_loaded_integration

from .const import DOMAIN
from .coordinator import ApplianceDataUpdateCoordinator
from .data import ApplianceConfig, CustomApplianceData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import CustomApplianceConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CustomApplianceConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    # Parse appliances from config data
    appliances_data = entry.data.get("appliances", {})
    appliances = {
        appliance_id: ApplianceConfig(
            name=config["name"],
            power_sensor_entity_id=config["power_sensor_entity_id"],
            area_id=config.get("area_id"),
            off_threshold=config["off_threshold"],
            running_threshold=config["running_threshold"],
            debounce_time=config["debounce_time"],
            complete_timeout=config["complete_timeout"],
        )
        for appliance_id, config in appliances_data.items()
    }

    # Create coordinator
    coordinator = ApplianceDataUpdateCoordinator(hass, appliances)

    # Set up runtime data
    entry.runtime_data = CustomApplianceData(
        appliances=appliances,
        coordinator=coordinator,
        integration=async_get_loaded_integration(hass, entry.domain),
    )

    # Initialize coordinator
    await coordinator.async_setup()

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: CustomApplianceConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    # Shutdown coordinator
    await entry.runtime_data.coordinator.async_shutdown()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: CustomApplianceConfigEntry,
) -> None:
    """Reload config entry."""
    # Parse new appliances configuration
    appliances_data = entry.data.get("appliances", {})
    new_appliances = {
        appliance_id: ApplianceConfig(
            name=config["name"],
            power_sensor_entity_id=config["power_sensor_entity_id"],
            area_id=config.get("area_id"),
            off_threshold=config["off_threshold"],
            running_threshold=config["running_threshold"],
            debounce_time=config["debounce_time"],
            complete_timeout=config["complete_timeout"],
        )
        for appliance_id, config in appliances_data.items()
    }

    # Update coordinator with new appliances
    coordinator = entry.runtime_data.coordinator
    await coordinator.async_update_appliances(new_appliances)

    # Update runtime data
    entry.runtime_data.appliances = new_appliances

    # Reload the entry to refresh entities
    await hass.config_entries.async_reload(entry.entry_id)
