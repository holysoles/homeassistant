"""Tests for Samsung ExLink actions."""

import pytest
from pytest_homeassistant.common import MockConfigEntry
from samsung_exlink import SamsungTVError

from homeassistant.components.samsung_exlink.const import DOMAIN
from homeassistant.components.samsung_exlink.services import (
    SamsungExLinkService,
    SamsungExLinkServiceArgument,
)
from homeassistant.const import CommonServiceArgument
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .conftest import MockSamsungTV


@pytest.fixture(autouse=True)
async def auto_init_components(init_components: None) -> None:
    """Set up the component."""


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        pytest.param(b"\x03\x0c\xf1", "030cf1", id="ack"),
        pytest.param(b"\x03\x0c\xff", "030cff", id="nack"),
    ],
)
async def test_send_raw_command(
    hass: HomeAssistant,
    mock_samsung_tv: MockSamsungTV,
    mock_config_entry: MockConfigEntry,
    reply: bytes,
    expected: str,
) -> None:
    """Test the raw bytes are sent and the TV reply is returned as hex."""
    mock_samsung_tv.send_raw.return_value = reply

    response = await hass.services.async_call(
        DOMAIN,
        SamsungExLinkService.SEND_RAW_COMMAND,
        {
            CommonServiceArgument.CONFIG_ENTRY_ID: mock_config_entry.entry_id,
            SamsungExLinkServiceArgument.CMD1: 0x0D,
            SamsungExLinkServiceArgument.CMD2: 0,
            SamsungExLinkServiceArgument.CMD3: 0,
            SamsungExLinkServiceArgument.VALUE: 0x1A,
        },
        blocking=True,
        return_response=True,
    )

    mock_samsung_tv.send_raw.assert_awaited_once_with(0x0D, 0, 0, 0x1A)
    assert response == {"reply": expected}


@pytest.mark.parametrize(
    "field",
    [
        SamsungExLinkServiceArgument.CMD1,
        SamsungExLinkServiceArgument.CMD2,
        SamsungExLinkServiceArgument.CMD3,
        SamsungExLinkServiceArgument.VALUE,
    ],
)
@pytest.mark.parametrize("byte", [-1, 256])
async def test_send_raw_command_validates_byte_range(
    hass: HomeAssistant,
    mock_samsung_tv: MockSamsungTV,
    mock_config_entry: MockConfigEntry,
    field: SamsungExLinkServiceArgument,
    byte: int,
) -> None:
    """Test every command byte must be in the unsigned-byte range."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SamsungExLinkService.SEND_RAW_COMMAND,
            {
                CommonServiceArgument.CONFIG_ENTRY_ID: mock_config_entry.entry_id,
                SamsungExLinkServiceArgument.CMD1: 0,
                SamsungExLinkServiceArgument.CMD2: 0,
                SamsungExLinkServiceArgument.CMD3: 0,
                SamsungExLinkServiceArgument.VALUE: 0,
                field: byte,
            },
            blocking=True,
            return_response=True,
        )

    mock_samsung_tv.send_raw.assert_not_awaited()


@pytest.mark.parametrize(
    "exception",
    [
        pytest.param(SamsungTVError("unexpected response"), id="library"),
        pytest.param(ConnectionError("connection lost"), id="connection"),
    ],
)
async def test_send_raw_command_translates_errors(
    hass: HomeAssistant,
    mock_samsung_tv: MockSamsungTV,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
) -> None:
    """Test transport and library errors use the integration error mapping."""
    mock_samsung_tv.send_raw.side_effect = exception

    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            DOMAIN,
            SamsungExLinkService.SEND_RAW_COMMAND,
            {
                CommonServiceArgument.CONFIG_ENTRY_ID: mock_config_entry.entry_id,
                SamsungExLinkServiceArgument.CMD1: 0x0D,
                SamsungExLinkServiceArgument.CMD2: 0,
                SamsungExLinkServiceArgument.CMD3: 0,
                SamsungExLinkServiceArgument.VALUE: 0x1A,
            },
            blocking=True,
            return_response=True,
        )

    assert err.value.translation_key == "command_failed"
    mock_samsung_tv.send_raw.assert_awaited_once_with(0x0D, 0, 0, 0x1A)
