"""Binary sensor platform for custom_appliance."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .entity import CustomApplianceEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import ApplianceDataUpdateCoordinator
    from .data import CustomApplianceConfigEntry


BINARY_SENSOR_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="is_running",
        name="Running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:play",
    ),
    BinarySensorEntityDescription(
        key="is_complete",
        name="Complete",
        icon="mdi:check-circle",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: CustomApplianceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator = entry.runtime_data.coordinator

    entities = []
    for appliance_id in coordinator.get_appliance_ids():
        for description in BINARY_SENSOR_DESCRIPTIONS:
            entities.append(
                CustomApplianceBinarySensor(
                    coordinator=coordinator,
                    appliance_id=appliance_id,
                    entity_description=description,
                )
            )

    async_add_entities(entities)


class CustomApplianceBinarySensor(CustomApplianceEntity, BinarySensorEntity):
    """Custom appliance binary sensor class."""

    def __init__(
        self,
        coordinator: ApplianceDataUpdateCoordinator,
        appliance_id: str,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor class."""
        super().__init__(coordinator, appliance_id, entity_description.key)
        self.entity_description = entity_description
        self._attr_name = entity_description.name

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.appliance_data:
            return None

        return self.appliance_data.get(self.entity_description.key, False)
