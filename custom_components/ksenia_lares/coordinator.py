"""The Ksenia Lares data update coordinator."""

from datetime import datetime, timedelta
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
        self,
        hass: HomeAssistant,
        client: LaresBase,
        scan_interval: int,
        scan_interval_zones: int,
        scan_interval_partitions: int,
        scan_interval_temperatures: int,
        scan_interval_outputs: int,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ksenia Lares",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self._scan_interval_zones = scan_interval_zones
        self._scan_interval_partitions = scan_interval_partitions
        self._scan_interval_temperatures = scan_interval_temperatures
        self._scan_interval_outputs = scan_interval_outputs

        # Track last update times
        self._last_zones_update = None
        self._last_partitions_update = None
        self._last_temperatures_update = None
        self._last_outputs_update = None

    def _should_update(self, last_update: datetime | None, interval: int) -> bool:
        """Check if data should be updated based on interval."""
        if last_update is None:
            return True
        return (datetime.now() - last_update).total_seconds() >= interval

    async def _async_update_data(self) -> dict:
        """Fetch data from Ksenia Lares client."""
        try:
            async with timeout(DEFAULT_TIMEOUT):
                _LOGGER.debug("Fetching data from Lares device")

                # Update zones if interval passed
                zones = None
                if self._should_update(
                    self._last_zones_update, self._scan_interval_zones
                ):
                    zones = await self.client.zones()
                    self._last_zones_update = datetime.now()
                    _LOGGER.debug("Updated zones data")
                elif self.data and DATA_ZONES in self.data:
                    zones = self.data[DATA_ZONES]

                # Update partitions if interval passed
                partitions = None
                if self._should_update(
                    self._last_partitions_update, self._scan_interval_partitions
                ):
                    partitions = await self.client.partitions()
                    self._last_partitions_update = datetime.now()
                    _LOGGER.debug("Updated partitions data")
                elif self.data and DATA_PARTITIONS in self.data:
                    partitions = self.data[DATA_PARTITIONS]

                # Update temperatures if interval passed
                temperatures = None
                if self._should_update(
                    self._last_temperatures_update, self._scan_interval_temperatures
                ):
                    temperatures = await self.client.temperatures()
                    self._last_temperatures_update = datetime.now()
                    _LOGGER.debug("Updated temperatures data")
                elif self.data and DATA_TEMPERATURES in self.data:
                    temperatures = self.data[DATA_TEMPERATURES]

                # Update outputs if interval passed
                outputs = None
                if self._should_update(
                    self._last_outputs_update, self._scan_interval_outputs
                ):
                    outputs = await self.client.outputs()
                    self._last_outputs_update = datetime.now()
                    _LOGGER.debug("Updated outputs data")
                elif self.data and DATA_OUTPUTS in self.data:
                    outputs = self.data[DATA_OUTPUTS]

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
        except TimeoutError as err:
            _LOGGER.error("Timeout fetching data from Lares device")
            raise UpdateFailed(f"Timeout communicating with device: {err}") from err
        except (OSError, ConnectionError) as err:
            _LOGGER.error("Network error fetching data: %s", err)
            raise UpdateFailed(f"Network error: {err}") from err
        except (KeyError, AttributeError, TypeError) as err:
            _LOGGER.error("Invalid data structure from Lares device: %s", err)
            raise UpdateFailed(f"Invalid data received: {err}") from err
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(
                "Unexpected error fetching data from Lares device: %s",
                err,
                exc_info=True,
            )
            raise UpdateFailed(f"Error communicating with device: {err}") from err
