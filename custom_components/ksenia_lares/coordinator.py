"""The Ksenia Lares data update coordinator."""

# import async_timeout
import asyncio
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

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
        async with asyncio.timeout(DEFAULT_TIMEOUT):
            zones = await self.client.zones()
            partitions = await self.client.partitions()
            temperatures = await self.client.temperatures()
            outputs = await self.client.outputs()

            return {
                DATA_ZONES: zones,
                DATA_PARTITIONS: partitions,
                DATA_TEMPERATURES: temperatures,
                DATA_OUTPUTS: outputs,
            }
