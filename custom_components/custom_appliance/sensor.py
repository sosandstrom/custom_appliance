"""Sensor platform for custom_appliance."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfPower, UnitOfTime

from .entity import CustomApplianceEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import ApplianceDataUpdateCoordinator
    from .data import CustomApplianceConfigEntry


SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="state",
        name="State",
        icon="mdi:state-machine",
    ),
    SensorEntityDescription(
        key="power",
        name="Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        icon="mdi:flash",
    ),
    SensorEntityDescription(
        key="time_in_state",
        name="Time in State",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:timer",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: CustomApplianceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator

    entities = []
    for appliance_id in coordinator.get_appliance_ids():
        for description in SENSOR_DESCRIPTIONS:
            entities.append(
                CustomApplianceSensor(
                    coordinator=coordinator,
                    appliance_id=appliance_id,
                    entity_description=description,
                )
            )

    async_add_entities(entities)


class CustomApplianceSensor(CustomApplianceEntity, SensorEntity):
    """Custom appliance sensor class."""

    def __init__(
        self,
        coordinator: ApplianceDataUpdateCoordinator,
        appliance_id: str,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator, appliance_id, entity_description.key)
        self.entity_description = entity_description
        self._attr_name = entity_description.name

    @property
    def native_value(self) -> str | float | int | None:
        """Return the native value of the sensor."""
        if not self.appliance_data:
            return None

        return self.appliance_data.get(self.entity_description.key)
