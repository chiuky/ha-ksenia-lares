"""The Ksenia Lares Alarm integration."""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .base import LaresBase
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL_OUTPUTS,
    CONF_SCAN_INTERVAL_PARTITIONS,
    CONF_SCAN_INTERVAL_TEMPERATURES,
    CONF_SCAN_INTERVAL_ZONES,
    DATA_COORDINATOR,
    DATA_UPDATE_LISTENER,
    DEFAULT_SCAN_INTERVAL_OUTPUTS,
    DEFAULT_SCAN_INTERVAL_PARTITIONS,
    DEFAULT_SCAN_INTERVAL_TEMPERATURES,
    DEFAULT_SCAN_INTERVAL_ZONES,
    DOMAIN,
)
from .coordinator import LaresDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ksenia Lares Alarm from a config entry."""
    _LOGGER.info("Setting up Ksenia Lares integration for %s", entry.data.get("host"))

    try:
        client = LaresBase(entry.data)
        scan_interval = entry.data[CONF_SCAN_INTERVAL]

        # Get scan intervals from options or data with fallback to defaults
        scan_interval_zones = entry.options.get(
            CONF_SCAN_INTERVAL_ZONES,
            entry.data.get(CONF_SCAN_INTERVAL_ZONES, DEFAULT_SCAN_INTERVAL_ZONES)
        )
        scan_interval_partitions = entry.options.get(
            CONF_SCAN_INTERVAL_PARTITIONS,
            entry.data.get(CONF_SCAN_INTERVAL_PARTITIONS, DEFAULT_SCAN_INTERVAL_PARTITIONS)
        )
        scan_interval_temperatures = entry.options.get(
            CONF_SCAN_INTERVAL_TEMPERATURES,
            entry.data.get(CONF_SCAN_INTERVAL_TEMPERATURES, DEFAULT_SCAN_INTERVAL_TEMPERATURES)
        )
        scan_interval_outputs = entry.options.get(
            CONF_SCAN_INTERVAL_OUTPUTS,
            entry.data.get(CONF_SCAN_INTERVAL_OUTPUTS, DEFAULT_SCAN_INTERVAL_OUTPUTS)
        )

        coordinator = LaresDataUpdateCoordinator(
            hass,
            client,
            scan_interval,
            scan_interval_zones,
            scan_interval_partitions,
            scan_interval_temperatures,
            scan_interval_outputs,
        )

        # Preload device info to verify connection
        device_info = await client.device_info()
        if device_info is None:
            _LOGGER.error("Failed to retrieve device info from %s", entry.data.get("host"))
            raise ConfigEntryNotReady("Unable to connect to Lares device")

        _LOGGER.debug("Successfully connected to Lares device: %s", device_info.get("name"))

    except (KeyError, ValueError, TypeError) as err:
        _LOGGER.error("Invalid configuration data: %s", err, exc_info=True)
        raise ConfigEntryNotReady(f"Invalid configuration: {err}") from err
    except (OSError, TimeoutError) as err:
        _LOGGER.error("Network error connecting to Lares device: %s", err)
        raise ConfigEntryNotReady(f"Network error: {err}") from err
    except Exception as err:
        _LOGGER.error("Unexpected error setting up Ksenia Lares: %s", err, exc_info=True)
        raise ConfigEntryNotReady(f"Failed to setup Lares device: {err}") from err

    unsub_options_update_listener = entry.add_update_listener(options_update_listener)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_UPDATE_LISTENER: unsub_options_update_listener,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    _LOGGER.info("Reloading Ksenia Lares integration due to options update")
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Ksenia Lares integration")

    unload_ok = all(
        await asyncio.gather(
            *(
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            )
        )
    )

    if unload_ok:
        hass.data[DOMAIN][entry.entry_id][DATA_UPDATE_LISTENER]()
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Ksenia Lares integration unloaded successfully")
    else:
        _LOGGER.warning("Failed to unload some Ksenia Lares platforms")

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.info("Migrating Ksenia Lares config entry from version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.data}
        new["port"] = 80

        hass.config_entries.async_update_entry(config_entry, data=new, version=2)
        _LOGGER.info("Migration to version 2 successful")

    if config_entry.version == 2:
        new = {**config_entry.data}
        # Add default scan intervals if not present
        if CONF_SCAN_INTERVAL_ZONES not in new:
            new[CONF_SCAN_INTERVAL_ZONES] = DEFAULT_SCAN_INTERVAL_ZONES
        if CONF_SCAN_INTERVAL_PARTITIONS not in new:
            new[CONF_SCAN_INTERVAL_PARTITIONS] = DEFAULT_SCAN_INTERVAL_PARTITIONS
        if CONF_SCAN_INTERVAL_TEMPERATURES not in new:
            new[CONF_SCAN_INTERVAL_TEMPERATURES] = DEFAULT_SCAN_INTERVAL_TEMPERATURES
        if CONF_SCAN_INTERVAL_OUTPUTS not in new:
            new[CONF_SCAN_INTERVAL_OUTPUTS] = DEFAULT_SCAN_INTERVAL_OUTPUTS

        hass.config_entries.async_update_entry(config_entry, data=new, version=3)
        _LOGGER.info("Migration to version 3 successful")

    return True
