# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom component template/blueprint called "Custom Appliance" designed to help developers create new Home Assistant integrations. It's not meant for end users but as a starting point for custom component development.

## Development Commands

- **Setup development environment**: `scripts/setup` - Installs Python dependencies from requirements.txt
- **Start development server**: `scripts/develop` - Runs Home Assistant with the custom component in debug mode using the config directory
- **Lint code**: `scripts/lint` - Runs ruff formatter and checker with auto-fix

## Architecture

### Core Structure
- **Domain**: `custom_appliance` - The integration domain identifier
- **Platforms**: Supports sensor, binary_sensor, and switch platforms
- **API Client**: `api.py` - Handles external API communication with authentication
- **Coordinator**: `coordinator.py` - Manages data updates using Home Assistant's DataUpdateCoordinator pattern
- **Config Flow**: `config_flow.py` - Handles UI-based configuration setup

### Key Components
- **Data Management**: Uses `IntegrationBlueprintData` class to store client, integration, and coordinator references
- **Update Interval**: Configured for 1-hour intervals in the coordinator
- **Authentication**: Supports username/password authentication through config flow
- **Error Handling**: Custom exceptions for API authentication and general errors

### File Structure
- `custom_components/custom_appliance/` - Main integration directory
- `config/` - Home Assistant configuration for development
- `scripts/` - Development and maintenance scripts
- `manifest.json` - Integration metadata and requirements

## Development Notes

- Uses Home Assistant 2025.2.4
- Code style enforced with ruff (version 0.12.1)
- Integration type: "hub" with "calculated" IoT class
- Supports config flow for UI-based setup
- Template repository meant to be forked and customized