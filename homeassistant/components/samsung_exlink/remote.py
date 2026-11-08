"""Remote platform for the Samsung ExLink integration."""

from collections.abc import Iterable
from typing import Any, override

from samsung_exlink import Key

from homeassistant.components.remote import ATTR_NUM_REPEATS, RemoteEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, SamsungExLinkConfigEntry
from .helpers import catch_command_errors

PARALLEL_UPDATES = 1
KEY_MAP = {key.name: key for key in Key if key is not Key.KEY_FACTORY}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SamsungExLinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Samsung ExLink remote."""
    async_add_entities([SamsungExLinkRemote(config_entry)])


class SamsungExLinkRemote(RemoteEntity):
    """Representation of a Samsung TV remote controlled over ExLink."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False

    def __init__(self, config_entry: SamsungExLinkConfigEntry) -> None:
        """Initialize the remote."""
        self._tv = config_entry.runtime_data
        self._attr_unique_id = config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            manufacturer="Samsung",
            model=self._tv.model.name if self._tv.model else None,
        )

    @catch_command_errors
    @override
    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send one or more remote key commands to the TV."""
        keys = []
        for name in command:
            if name not in KEY_MAP:
                raise ServiceValidationError(f"Unsupported Samsung ExLink key: {name}")
            keys.append(KEY_MAP[name])

        for _ in range(kwargs[ATTR_NUM_REPEATS]):
            for key in keys:
                await self._tv.send_key(key)
