"""Actions for Samsung ExLink."""

from enum import StrEnum

import probatio

from homeassistant.const import CommonServiceArgument
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.helpers import config_validation as cv, service
from homeassistant.helpers.selector import ConfigEntrySelector
from homeassistant.helpers.service import async_register_admin_service

from .const import DOMAIN
from .helpers import catch_command_errors


class SamsungExLinkService(StrEnum):
    """Available Samsung ExLink actions."""

    SEND_RAW_COMMAND = "send_raw_command"


class SamsungExLinkServiceArgument(StrEnum):
    """Samsung ExLink action arguments."""

    CMD1 = "cmd1"
    CMD2 = "cmd2"
    CMD3 = "cmd3"
    VALUE = "value"


SERVICE_SCHEMA = probatio.Schema(
    {
        probatio.Required(CommonServiceArgument.CONFIG_ENTRY_ID): ConfigEntrySelector(
            {"integration": DOMAIN}
        ),
        probatio.Required(SamsungExLinkServiceArgument.CMD1): cv.byte,
        probatio.Required(SamsungExLinkServiceArgument.CMD2): cv.byte,
        probatio.Required(SamsungExLinkServiceArgument.CMD3): cv.byte,
        probatio.Required(SamsungExLinkServiceArgument.VALUE): cv.byte,
    }
)


@catch_command_errors
async def async_send_raw_command(call: ServiceCall) -> ServiceResponse:
    """Send a raw command to the TV and return its reply as hex."""
    entry = service.async_get_config_entry(
        call.hass, DOMAIN, call.data[CommonServiceArgument.CONFIG_ENTRY_ID]
    )
    reply = await entry.runtime_data.send_raw(
        call.data[SamsungExLinkServiceArgument.CMD1],
        call.data[SamsungExLinkServiceArgument.CMD2],
        call.data[SamsungExLinkServiceArgument.CMD3],
        call.data[SamsungExLinkServiceArgument.VALUE],
    )
    return {"reply": reply.hex()}


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register Samsung ExLink actions."""
    async_register_admin_service(
        hass,
        DOMAIN,
        SamsungExLinkService.SEND_RAW_COMMAND,
        async_send_raw_command,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
