"""Custom types for custom_appliance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .coordinator import ApplianceDataUpdateCoordinator


type CustomApplianceConfigEntry = ConfigEntry[CustomApplianceData]


@dataclass
class ApplianceConfig:
    """Configuration for a single appliance."""

    name: str
    power_sensor_entity_id: str
    area_id: str | None
    off_threshold: float
    running_threshold: float
    debounce_time: int
    complete_timeout: int


@dataclass
class CustomApplianceData:
    """Data for the Custom Appliance integration."""

    appliances: dict[str, ApplianceConfig]
    coordinator: ApplianceDataUpdateCoordinator
    integration: Integration
