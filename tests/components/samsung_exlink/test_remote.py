"""Tests for the Samsung ExLink remote platform."""

from unittest.mock import call

import pytest
from pytest_homeassistant.common import MockConfigEntry
from samsung_exlink import CommandRejected, Key, SamsungTVError

from homeassistant.components.remote import (
    ATTR_NUM_REPEATS,
    DOMAIN as REMOTE_DOMAIN,
    SERVICE_SEND_COMMAND,
)
from homeassistant.components.samsung_exlink.const import DOMAIN
from homeassistant.const import ATTR_COMMAND, ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .conftest import MockSamsungTV

ENTITY_ID = "remote.samsung_tv"


@pytest.fixture(autouse=True)
async def auto_init_components(init_components: None) -> None:
    """Set up the component."""


async def test_entities_created(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test the remote entity is created and associated with the TV device."""
    assert hass.states.get(ENTITY_ID) is not None
    entity = entity_registry.async_get(ENTITY_ID)
    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, mock_config_entry.entry_id), mock_config_entry.entry_id
    )
    assert entity is not None
    assert device is not None
    assert entity.device_id == device.id


async def test_send_command_repeats(
    hass: HomeAssistant, mock_samsung_tv: MockSamsungTV
) -> None:
    """Test commands are mapped to library keys and repeated in order."""
    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {
            ATTR_ENTITY_ID: ENTITY_ID,
            ATTR_COMMAND: ["KEY_POWER", "KEY_VOLUP"],
            ATTR_NUM_REPEATS: 2,
        },
        blocking=True,
    )

    assert mock_samsung_tv.send_key.await_args_list == [
        call(Key.KEY_POWER),
        call(Key.KEY_VOLUP),
        call(Key.KEY_POWER),
        call(Key.KEY_VOLUP),
    ]


async def test_service_key_is_not_supported(
    hass: HomeAssistant, mock_samsung_tv: MockSamsungTV
) -> None:
    """Test service-oriented keys are not available through the remote."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_SEND_COMMAND,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: "KEY_FACTORY"},
            blocking=True,
        )

    mock_samsung_tv.send_key.assert_not_awaited()


@pytest.mark.parametrize(
    ("exception", "translation_key"),
    [
        pytest.param(CommandRejected("rejected"), "command_rejected", id="rejected"),
        pytest.param(
            SamsungTVError("unexpected response"), "command_failed", id="library"
        ),
        pytest.param(
            ConnectionError("connection lost"), "command_failed", id="connection"
        ),
        pytest.param(TimeoutError(), "command_failed", id="timeout"),
    ],
)
async def test_send_command_error(
    hass: HomeAssistant,
    mock_samsung_tv: MockSamsungTV,
    exception: Exception,
    translation_key: str,
) -> None:
    """Test library and connection failures are translated consistently."""
    mock_samsung_tv.send_key.side_effect = exception

    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_SEND_COMMAND,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: "KEY_POWER"},
            blocking=True,
        )

    assert err.value.translation_key == translation_key
