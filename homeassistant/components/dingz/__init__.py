"""The dingz integration."""

from __future__ import annotations

import asyncio
import logging
import typing

from dingz.dingz import Dingz
from dingz.discovery import DiscoveredDevice, discover_dingz_devices

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import async_get, format_mac
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["cover", "sensor"]


class DingzDevice:
    """represents a single Dingz device."""

    def __init__(
        self,
        api: Dingz,
        identifiers: set[tuple[str, str]],
        connections: set[tuple[str, str]],
    ):
        """Initialize the dingz device."""
        self.api = api
        self.connections = connections
        self.identifiers = identifiers


DingzDeviceRegistry = typing.Dict[str, DingzDevice]


async def setup_device(
    hass: HomeAssistant, entry: ConfigEntry, discovered_device: DiscoveredDevice
) -> None:
    """Setups the dingz device and loads the api object."""
    formatted_mac = format_mac(discovered_device.mac)

    dingz_api = Dingz(discovered_device.host)

    await dingz_api.get_device_info()
    await dingz_api.get_info()
    await dingz_api.get_system_config()

    identifiers = {(DOMAIN, formatted_mac)}
    connections = {(dr.CONNECTION_NETWORK_MAC, formatted_mac)}

    device_registry = async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=connections,
        identifiers=identifiers,
        manufacturer="iolo AG",
        name=dingz_api.dingz_name,
        model=dingz_api.type,
        sw_version=dingz_api.version,
    )

    ding_device = DingzDevice(
        dingz_api, identifiers=identifiers, connections=connections
    )

    hass.data[DOMAIN][entry.entry_id][formatted_mac] = ding_device


async def discover_and_setup(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Discover all dingzes and set them up."""
    devices_by_mac: DingzDeviceRegistry = hass.data[DOMAIN][entry.entry_id]
    discovered_devices = await discover_dingz_devices()

    for discovered_device in discovered_devices:
        formatted_mac = format_mac(discovered_device.mac)
        if formatted_mac in devices_by_mac:
            _LOGGER.debug("device %s already set up", formatted_mac)
            continue
        await setup_device(hass, entry, discovered_device)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the dingz component."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up dingz from a config entry."""
    hass.data[DOMAIN][entry.entry_id] = {}
    await discover_and_setup(hass, entry)

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    dingzs: dict[str, DingzDevice] = hass.data[DOMAIN][entry.entry_id]

    for dingz_device in dingzs.values():
        await dingz_device.api.close()

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class DingzEntity(Entity):
    """Wrapper for a Dingz Device with Home Assistant specific functions."""

    api: Dingz

    def __init__(self, dingz: DingzDevice, entity_name: str):
        """Initialize the Dingz entity wrapper."""
        self.api = dingz.api
        self.dingz = dingz
        self._unique_id = f"{self.api.mac}-{entity_name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Dingz Device."""
        return {
            "identifiers": self.dingz.identifiers,
            "connections": self.dingz.connections,
        }
