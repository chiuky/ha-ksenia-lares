"""Base component for Lares."""

import logging

import aiohttp
from getmac import get_mac_address
from lxml import etree

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, format_mac

from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


class LaresBase:
    """The implementation of the Lares base class."""

    def __init__(self, data: dict) -> None:
        """Construct the class."""
        username = data["username"]
        password = data["password"]
        host = data["host"]
        port = data["port"]
        use_https = data.get("use_https", True)

        self._auth = aiohttp.BasicAuth(username, password)
        self._ip = host
        self._port = port
        scheme = "https" if use_https else "http"
        self._url = f"{scheme}://{host}:{self._port}"
        self._model = None
        self._zone_descriptions = None
        self._partition_descriptions = None
        self._scenario_descriptions = None
        self._temperature_indoor = None
        self._temperature_outdoor = None
        self._output_descriptions = None

    async def info(self) -> dict | None:
        """Get general info."""
        response = await self.get("info/generalInfo.xml")

        if response is None:
            _LOGGER.warning("Failed to retrieve device info from %s", self._url)
            return None

        try:
            mac = get_mac_address(ip=self._ip)
            unique_id = str(mac)

            if mac is None:
                _LOGGER.debug("MAC address not available, using IP:port as unique_id")
                unique_id = f"{self._ip}:{self._port}"

            return {
                "mac": mac,
                "id": unique_id,
                "name": response.xpath("/generalInfo/productName")[0].text,
                "info": response.xpath("/generalInfo/info1")[0].text,
                "version": response.xpath("/generalInfo/productHighRevision")[0].text,
                "revision": response.xpath("/generalInfo/productLowRevision")[0].text,
                "build": response.xpath("/generalInfo/productBuildRevision")[0].text,
            }
        except (IndexError, AttributeError) as err:
            _LOGGER.error("Error parsing device info XML: %s", err)
            return None

    async def device_info(self) -> dict | None:
        """Get device info."""
        device_info = await self.info()

        if device_info is None:
            return None

        info = {
            "identifiers": {(DOMAIN, device_info["id"])},
            "name": device_info["name"],
            "manufacturer": MANUFACTURER,
            "model": device_info["name"],
            "sw_version": f"{device_info['version']}\
                .{device_info['revision']}.{device_info['build']}",
            "configuration_url": self._url,
        }

        mac = device_info["mac"]

        if mac is not None:
            info["connections"] = {(CONNECTION_NETWORK_MAC, format_mac(mac))}

        return info

    async def zone_descriptions(self) -> list[str] | None:
        """Get available zones."""
        model = await self.get_model()
        if self._zone_descriptions is None:
            self._zone_descriptions = await self.get_descriptions(
                f"zones/zonesDescription{model}.xml", "/zonesDescription/zone"
            )

        return self._zone_descriptions

    async def zones(self) -> list[dict[str, str]] | None:
        """Get available zones."""
        model = await self.get_model()
        if model is None:
            _LOGGER.error("Unable to determine device model")
            return None

        response = await self.get(f"zones/zonesStatus{model}.xml")

        if response is None:
            _LOGGER.warning("Failed to retrieve zones status")
            return None

        try:
            zones = response.xpath("/zonesStatus/zone")
            return [
                {
                    "status": zone.find("status").text,
                    "bypass": zone.find("bypass").text,
                }
                for zone in zones
            ]
        except (AttributeError, TypeError) as err:
            _LOGGER.error("Error parsing zones XML: %s", err)
            return None

    async def output_descriptions(self) -> list[str] | None:
        """Get output descr zones."""
        model = await self.get_model()
        if self._output_descriptions is None:
            self._output_descriptions = await self.get_descriptions(
                f"outputs/outputsDescription{model}.xml", "/outputsDescription/output"
            )

        return self._output_descriptions

    async def outputs(self) -> list[dict[str, str]] | None:
        """Get available zones."""
        model = await self.get_model()
        if model is None:
            _LOGGER.error("Unable to determine device model for outputs")
            return None

        outputs_status = await self.get(f"outputs/outputsStatus{model}.xml")

        if outputs_status is None:
            _LOGGER.warning("Failed to retrieve outputs status")
            return None

        try:
            outputs = outputs_status.xpath("/outputsStatus/output")
            return [
                {
                    "status": output.find("status").text,
                    "type": output.find("type").text,
                    "value": output.find("value").text,
                    "noPIN": output.find("noPIN").text,
                }
                for output in outputs
            ]
        except (AttributeError, TypeError) as err:
            _LOGGER.error("Error parsing outputs XML: %s", err)
            return None

    async def temperatures(self) -> list[dict[str, str]] | None:
        """Get lares temperatures."""
        response = await self.get("state/laresStatus.xml")
        if response is None:
            _LOGGER.warning("Failed to retrieve temperatures")
            return None

        try:
            self._temperature_indoor = (
                response.xpath("/laresStatus/temperature/indoor")[0]
                .text.replace("C", "")
                .strip()
            )
            self._temperature_outdoor = (
                response.xpath("/laresStatus/temperature/outdoor")[0]
                .text.replace("C", "")
                .strip()
            )
            return [
                {
                    "description": "lares_temperature_indoor",
                    "temperatureValue": self._temperature_indoor,
                },
                {
                    "description": "lares_temperature_outdoor",
                    "temperatureValue": self._temperature_outdoor,
                },
            ]
        except (IndexError, AttributeError, TypeError) as err:
            _LOGGER.error("Error parsing temperatures XML: %s", err)
            return None

    async def partitions(self) -> list[dict[str, str]] | None:
        """Get status of partitions."""
        model = await self.get_model()
        if model is None:
            _LOGGER.error("Unable to determine device model for partitions")
            return None

        response = await self.get(f"partitions/partitionsStatus{model}.xml")

        if response is None:
            _LOGGER.warning("Failed to retrieve partitions status")
            return None

        try:
            partitions = response.xpath("/partitionsStatus/partition")
            return [
                {
                    "status": partition.text,
                }
                for partition in partitions
            ]
        except (AttributeError, TypeError) as err:
            _LOGGER.error("Error parsing partitions XML: %s", err)
            return None

    async def partition_descriptions(self) -> list[str] | None:
        """Get available partitions."""
        model = await self.get_model()

        if self._partition_descriptions is None:
            self._partition_descriptions = await self.get_descriptions(
                f"partitions/partitionsDescription{model}.xml",
                "/partitionsDescription/partition",
            )

        return self._partition_descriptions

    async def get_descriptions(self, path: str, element: str) -> list[str] | None:
        """Get descriptions."""
        response = await self.get(path)

        if response is None:
            _LOGGER.warning("Failed to retrieve descriptions from %s", path)
            return None

        try:
            content = response.xpath(element)
            return [item.text for item in content]
        except (AttributeError, TypeError) as err:
            _LOGGER.error("Error parsing descriptions from %s: %s", path, err)
            return None

    async def scenarios(self) -> list[dict[str, int | bool]] | None:
        """Get status of scenarios."""
        response = await self.get("scenarios/scenariosOptions.xml")

        if response is None:
            _LOGGER.warning("Failed to retrieve scenarios")
            return None

        try:
            scenarios = response.xpath("/scenariosOptions/scenario")
            return [
                {
                    "id": idx,
                    "enabled": scenario.find("abil").text == "TRUE",
                    "noPin": scenario.find("nopin").text == "TRUE",
                }
                for idx, scenario in enumerate(scenarios)
            ]
        except (AttributeError, TypeError) as err:
            _LOGGER.error("Error parsing scenarios XML: %s", err)
            return None

    async def scenario_descriptions(self) -> list[str] | None:
        """Get descriptions of scenarios."""
        if self._scenario_descriptions is None:
            self._scenario_descriptions = await self.get_descriptions(
                "scenarios/scenariosDescription.xml", "/scenariosDescription/scenario"
            )

        return self._scenario_descriptions

    async def activate_scenario(self, scenario: int, pin_code: str) -> bool:
        """Activate the given scenarios, requires the alarm code."""
        params = {"macroId": scenario}

        return await self.send_command("setMacro", pin_code, params)

    async def bypass_zone(self, zone_id: int, pin_code: str, bypass: bool) -> bool:
        """Activate the given scenarios, requires the alarm code."""
        params = {
            "zoneId": zone_id + 1,  # Lares uses index starting with 1
            "zoneValue": 1 if bypass else 0,
        }

        return await self.send_command("setByPassZone", pin_code, params)

    async def switch_output(self, output_id: int, pin_code: str, switch: bool) -> bool:
        """Activate the given scenarios, requires the alarm code."""
        params = {
            "outputId": output_id,  # Lares output uses index starting with 0
            "outputValue": 255 if switch else 0,
        }

        return await self.send_command("setOutput", pin_code, params)

    async def get_model(self) -> str:
        """Get model information."""
        if self._model is None:
            info = await self.info()
            if info is not None:
                if info["name"].endswith("128IP"):
                    self._model = "128IP"
                elif info["name"].endswith("48IP"):
                    self._model = "48IP"
                else:
                    self._model = "16IP"

        return self._model

    async def send_command(
        self, command: str, pin_code: str, params: dict[str, int]
    ) -> bool:
        """Send Command."""
        url_param = "".join(f"&{k}={v}" for k, v in params.items())
        path = f"cmd/cmdOk.xml?cmd={command}&pin={pin_code}\
        &redirectPage=/xml/cmd/cmdError.xml{url_param}"

        _LOGGER.debug("Sending command: %s with params: %s", command, params)

        try:
            response = await self.get(path)
            if response is None:
                _LOGGER.error("Failed to send command %s: no response", command)
                return False

            cmd = response.xpath("/cmd")

            if cmd is None or len(cmd) == 0 or cmd[0].text != "cmdSent":
                _LOGGER.error(
                    "Command %s failed: %s",
                    command,
                    cmd[0].text if cmd and len(cmd) > 0 else "no response",
                )
                return False

            _LOGGER.info("Command %s executed successfully", command)
            return True
        except (IndexError, AttributeError) as err:
            _LOGGER.error("Error parsing command response for %s: %s", command, err)
            return False
        except (OSError, TimeoutError) as err:
            _LOGGER.error("Network error executing command %s: %s", command, err)
            return False

    async def get(self, path: str) -> etree._Element | None:  # pylint: disable=c-extension-no-member
        """Get method."""
        url = f"{self._url}/xml/{path}"

        try:
            async with (
                aiohttp.ClientSession(auth=self._auth) as session,
                session.get(url=url) as response,
            ):
                if response.status != 200:
                    _LOGGER.warning(
                        "HTTP error %s when accessing %s", response.status, url
                    )
                    return None

                xml = await response.read()
                if not xml:
                    _LOGGER.warning("Empty response from %s", url)
                    return None

                parser = etree.XMLParser(resolve_entities=False)  # pylint: disable=c-extension-no-member
                return etree.fromstring(xml, parser=parser)  # pylint: disable=c-extension-no-member

        except aiohttp.ClientConnectorError as conn_err:
            _LOGGER.warning(
                "Connection error to %s: %s - Check device availability",
                self._url,
                str(conn_err),
            )
        except aiohttp.ClientError as client_err:
            _LOGGER.warning("Client error accessing %s: %s", self._url, str(client_err))
        except etree.XMLSyntaxError as xml_err:  # pylint: disable=c-extension-no-member
            _LOGGER.error(
                "XML parsing error from %s: %s - Device may have returned invalid data",
                self._url,
                str(xml_err),
            )
        except (OSError, TimeoutError) as err:
            _LOGGER.warning(
                "Network timeout or OS error accessing %s: %s",
                self._url,
                str(err),
            )
        except ValueError as err:
            _LOGGER.error(
                "Invalid response data from %s: %s",
                self._url,
                str(err),
            )
        except RuntimeError as err:
            # Covers unexpected runtime issues without masking system-exiting exceptions
            _LOGGER.error("Runtime error accessing %s: %s", self._url, err)
        return None
