"""Dingz sensors."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_TEMPERATURE,
    LIGHT_LUX,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DingzDevice, DingzDeviceRegistry, DingzEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for device."""
    dingzs: DingzDeviceRegistry = hass.data[DOMAIN][entry.entry_id]
    entities: list[Entity] = []
    for dingz in dingzs.values():
        entities.append(DingzTemperatureSensor(dingz))
        entities.append(DingzIlluminanceSensor(dingz))

    async_add_entities(entities, update_before_add=True)


class DingzIlluminanceSensor(DingzEntity):
    """Integrated illumination sensor of the Dingz unit."""

    def __init__(self, dingz: DingzDevice):
        """Initialize an illumination sensor."""
        super().__init__(dingz, "lux")
        self._illuminance = None

    async def async_update(self) -> None:
        """Update state of sensor."""
        await self.api.get_light()
        self._illuminance = self.api.intensity

    @property
    def name(self) -> str:
        """Name of sensor."""
        return f"{self.api.dingz_name} Illumination"

    @property
    def state(self) -> int | None:
        """Return illumination in lux."""
        return self._illuminance

    @property
    def unit_of_measurement(self) -> str | None:
        """Return unit of sensor."""
        return LIGHT_LUX

    @property
    def device_class(self) -> str | None:
        """Return device class."""
        return DEVICE_CLASS_ILLUMINANCE


class DingzTemperatureSensor(DingzEntity, SensorEntity):
    """Integrated temperature sensor of the Dingz unit."""

    def __init__(self, dingz: DingzDevice):
        """Initialize a temperature sensor."""
        super().__init__(dingz, "roomtemp")
        self._temperature = None

    async def async_update(self) -> None:
        """Update internal state of temperature sensor."""
        await self.api.get_temperature()
        self._temperature = self.api.temperature

    @property
    def name(self) -> str:
        """Name of sensor."""
        return f"{self.api.dingz_name} Temperature"

    @property
    def state(self) -> int | None:
        """Return temperature in celsius."""
        return self._temperature

    @property
    def unit_of_measurement(self) -> str | None:
        """Return unit of temperature."""
        return TEMP_CELSIUS

    @property
    def device_class(self) -> str | None:
        """Return device class."""
        return DEVICE_CLASS_TEMPERATURE
