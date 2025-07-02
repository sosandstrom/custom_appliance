# Custom Appliance State Machine Specification v1

## Overview

This specification defines a Home Assistant custom integration that monitors appliances through power consumption patterns. Users can configure multiple appliances, each with custom power thresholds to detect appliance states.

## Architecture

### Multi-Appliance Support
- Single integration instance supports multiple appliances
- Each appliance becomes a separate Home Assistant device
- Each appliance monitors its own power sensor entity
- Appliances can be assigned to specific areas in Home Assistant

### State Machine

#### States
- **OFF**: Appliance is completely off (power below off_threshold)
- **IDLE**: Appliance is on but not actively running (power between off_threshold and running_threshold)  
- **RUNNING**: Appliance is actively operating (power above running_threshold)
- **COMPLETE**: Appliance has finished a cycle (transitioned from RUNNING to IDLE/OFF)

#### State Transitions
```
OFF ←→ IDLE ←→ RUNNING → COMPLETE → IDLE
```

#### Power Thresholds (User Configurable)
- `off_threshold`: Maximum power when appliance is off (default: 5W)
- `running_threshold`: Minimum power when appliance is running (default: 50W)
- Power between thresholds indicates IDLE state

#### Timing Parameters (User Configurable)
- `debounce_time`: Minimum time in state before transition (default: 60s)
- `complete_timeout`: Time in IDLE after RUNNING to trigger COMPLETE (default: 300s)

## Configuration

### Per Appliance Settings
- **Name**: User-friendly appliance name
- **Power Sensor**: Entity ID of existing power sensor (supports single-phase or three-phase totals)
- **Area**: Home Assistant area assignment for the appliance device
- **Power Thresholds**: off_threshold, running_threshold
- **Timing**: debounce_time, complete_timeout

### Config Flow
- Initial setup creates first appliance
- Options flow allows adding/editing/removing appliances
- Validation ensures unique names and valid power sensor entities

## Entities Per Appliance

Each appliance creates a Home Assistant device with these entities:

### Sensor Entities
- **State Sensor**: Current appliance state (OFF/IDLE/RUNNING/COMPLETE)
- **Power Sensor**: Current power consumption (from monitored sensor)
- **Time in State**: Duration in current state

### Binary Sensor Entities  
- **Is Running**: True when state is RUNNING
- **Is Complete**: True when state is COMPLETE

## Implementation Notes

### Power Monitoring
- Integration subscribes to power sensor state changes
- State transitions based on sustained power levels (debounced)
- Handles sensor unavailability gracefully
- Supports both single-phase and three-phase power sensors

### Device Management
- Each appliance registered as separate Home Assistant device
- Device assigned to user-selected area
- Unique device identifiers prevent conflicts

### Error Handling
- Invalid power readings ignored
- Sensor unavailability doesn't crash integration
- Configuration validation prevents invalid setups