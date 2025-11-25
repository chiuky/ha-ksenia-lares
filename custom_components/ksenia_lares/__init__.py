"""The Ksenia Lares Alarm integration."""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .base import LaresBase
from .const import CONF_SCAN_INTERVAL, DATA_COORDINATOR, DATA_UPDATE_LISTENER, DOMAIN
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
        coordinator = LaresDataUpdateCoordinator(hass, client, scan_interval)

        # Preload device info to verify connection
        device_info = await client.device_info()
        if device_info is None:
            _LOGGER.error("Failed to retrieve device info from %s", entry.data.get("host"))
            raise ConfigEntryNotReady("Unable to connect to Lares device")

        _LOGGER.debug("Successfully connected to Lares device: %s", device_info.get("name"))

    except Exception as err:
        _LOGGER.error("Error setting up Ksenia Lares: %s", err, exc_info=True)
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

        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)
        _LOGGER.info("Migration to version 2 successful")

    return True
