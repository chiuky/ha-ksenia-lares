"""The Ksenia Lares Alarm integration."""

import asyncio

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .base import LaresBase
from .const import CONF_SCAN_INTERVAL, DATA_COORDINATOR, DATA_UPDATE_LISTENER, DOMAIN
from .coordinator import LaresDataUpdateCoordinator

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ksenia Lares Alarm from a config entry."""

    client = LaresBase(entry.data)
    scan_interval = entry.data[CONF_SCAN_INTERVAL]
    coordinator = LaresDataUpdateCoordinator(hass, client, scan_interval)

    # Preload device info
    await client.device_info()

    unsub_options_update_listener = entry.add_update_listener(options_update_listener)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_UPDATE_LISTENER: unsub_options_update_listener,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return bool(1)  # True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
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

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""

    if config_entry.version == 1:
        new = {**config_entry.data}
        new["port"] = 80

        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    return bool(1)  # True
