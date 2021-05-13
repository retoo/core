"""Support for Cover devices."""

from __future__ import annotations

from typing import Any

from dingz.shade import Shade

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverEntity,
)
from homeassistant.config_entries import ConfigEntry
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
    """Set up covers."""
    dingzs: DingzDeviceRegistry = hass.data[DOMAIN][entry.entry_id]
    entities: list[Entity] = []
    for dingz in dingzs.values():
        await dingz.api.get_devices_config()
        for shade in dingz.api.shades.all():
            entities.append(DingzCover(dingz, shade))

    async_add_entities(entities, True)


class DingzCover(DingzEntity, CoverEntity):
    """Represents a cover controller by the dingz unti."""

    def __init__(self, dingz: DingzDevice, shade: Shade):
        """Initialize dingz cover."""
        super().__init__(dingz, f"cover-{shade.absolute_index}")
        self.shade = shade
        self._current_cover_position = None
        self._current_tilt_position = None
        self._is_closed = None
        self._is_opened = None
        self._is_opening = None
        self._is_closing = None
        self._name = self.shade.name

    @property
    def name(self) -> str | None:
        """Name of cover."""
        return f"{self.api.dingz_name} {self._name}"

    async def async_update(self) -> None:
        """Update state of cover."""
        await self.api.get_state()
        self._is_closed = self.shade.is_shade_closed()
        self._is_opened = self.shade.is_shade_opened()
        self._current_cover_position = self.shade.current_blind_level()
        self._current_tilt_position = self.shade.current_lamella_level()
        self._is_opening = self.shade.is_shade_opening()
        self._is_closing = self.shade.is_shade_closing()

    @property
    def current_cover_position(self) -> int | None:
        """Position of the cover."""
        return self._current_cover_position

    @property
    def current_cover_tilt_position(self) -> int | None:
        """Return the current tilt position of cover."""
        return self._current_tilt_position

    @property
    def is_opening(self) -> bool | None:
        """Return if the cover is opening."""
        return self._is_opening

    @property
    def is_closing(self) -> bool | None:
        """Return if the cover is closing."""
        return self._is_closing

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is cloed."""
        return self._is_closed

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.shade.shade_up()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        await self.shade.shade_down()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.shade.shade_stop()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        await self.shade.operate_shade(blind=kwargs[ATTR_POSITION])

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the cover tilt."""
        await self.shade.lamella_open()

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the cover tilt."""
        await self.shade.lamella_close()

    async def async_stop_cover_tilt(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.shade.lamella_stop()

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position."""
        await self.shade.operate_shade(lamella=kwargs[ATTR_TILT_POSITION])
