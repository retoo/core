"""Config flow for dingz."""

from dingz.discovery import discover_dingz_devices

from homeassistant.helpers import config_entry_flow

from .const import DOMAIN


async def _async_has_devices() -> bool:
    """Return if there are devices that can be discovered."""
    devices = await discover_dingz_devices()
    return bool(len(devices) > 0)


config_entry_flow.register_discovery_flow(DOMAIN, "dingz", _async_has_devices)
