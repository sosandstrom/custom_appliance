"""Custom Appliance Entity base class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import ApplianceDataUpdateCoordinator


class CustomApplianceEntity(CoordinatorEntity[ApplianceDataUpdateCoordinator]):
    """Base entity for custom appliance."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ApplianceDataUpdateCoordinator,
        appliance_id: str,
        entity_key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._appliance_id = appliance_id
        self._entity_key = entity_key

        config = coordinator.get_appliance_config(appliance_id)
        if config is None:
            raise ValueError(f"Appliance {appliance_id} not found")

        self._appliance_config = config

        # Set unique ID for this entity
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{appliance_id}_{entity_key}"
        )

        # Set device info - each appliance becomes its own device
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, f"{coordinator.config_entry.entry_id}_{appliance_id}")
            },
            name=config.name,
            model="Custom Appliance",
            manufacturer="Custom Appliance Integration",
            via_device=(DOMAIN, coordinator.config_entry.entry_id),
        )

        # Set area if configured
        if config.area_id:
            self._attr_device_info["suggested_area"] = config.area_id

    @property
    def appliance_data(self) -> dict[str, any] | None:
        """Get appliance data from coordinator."""
        return (
            self.coordinator.data.get(self._appliance_id)
            if self.coordinator.data
            else None
        )
