"""The Ksenia Lares data update coordinator."""

import asyncio
from datetime import timedelta
import logging

from async_timeout import timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .base import LaresBase
from .const import (
    DATA_OUTPUTS,
    DATA_PARTITIONS,
    DATA_TEMPERATURES,
    DATA_ZONES,
    DEFAULT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class LaresDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinate for data updates from Ksenia Lares."""

    def __init__(
        self, hass: HomeAssistant, client: LaresBase, scan_interval: int
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ksenia Lares",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch data from Ksenia Lares client."""
        try:
            async with timeout(DEFAULT_TIMEOUT):
                _LOGGER.debug("Fetching data from Lares device")

                zones = await self.client.zones()
                partitions = await self.client.partitions()
                temperatures = await self.client.temperatures()
                outputs = await self.client.outputs()

                # Validate that we got some data
                if zones is None and partitions is None:
                    _LOGGER.warning("No data received from Lares device")
                    raise UpdateFailed("Failed to fetch data from device")

                _LOGGER.debug(
                    "Successfully fetched data: %d zones, %d partitions, %d outputs",
                    len(zones) if zones else 0,
                    len(partitions) if partitions else 0,
                    len(outputs) if outputs else 0,
                )

                return {
                    DATA_ZONES: zones,
                    DATA_PARTITIONS: partitions,
                    DATA_TEMPERATURES: temperatures,
                    DATA_OUTPUTS: outputs,
                }
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout fetching data from Lares device")
            raise UpdateFailed(f"Timeout communicating with device: {err}") from err
        except (OSError, ConnectionError) as err:
            _LOGGER.error("Network error fetching data: %s", err)
            raise UpdateFailed(f"Network error: {err}") from err
        except (KeyError, AttributeError, TypeError) as err:
            _LOGGER.error("Invalid data structure from Lares device: %s", err)
            raise UpdateFailed(f"Invalid data received: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error fetching data from Lares device: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with device: {err}") from err
