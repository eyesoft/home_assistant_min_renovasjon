"""
Support for GoGoGate2 device.

For more details about this component, please refer to the documentation at
https://home-assistant.io/...
"""

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_IP_ADDRESS, CONF_NAME)

REQUIREMENTS = ['pygogogate2==0.1.1']

_LOGGER = logging.getLogger(__name__)

DOMAIN = "gogogate2"
DEFAULT_NAME = 'gogogate2'
DATA_GOGOGATE2 = "data_gogogate2"

NOTIFICATION_ID = 'gogogate2_notification'
NOTIFICATION_TITLE = 'Gogogate2 Cover Setup'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


# noinspection PyUnresolvedReferences,PyPep8Naming
async def async_setup(hass, config):
    """Set up the Gogogate2 component."""
    from pygogogate2 import Gogogate2API as pygogogate2

    ip_address = config.get(CONF_IP_ADDRESS)
    password = config.get(CONF_PASSWORD)
    username = config.get(CONF_USERNAME)

    mygogogate2_list = []

    mygogogate2 = pygogogate2(username, password, ip_address)
    hass.data[DOMAIN] = mygogogate2

    try:
        devices = mygogogate2.get_devices()
        if devices is False:
            raise ValueError(
                "Username or Password is incorrect or no devices found")

        mygogogate2_list.append(door for door in devices)

    except (TypeError, KeyError, NameError, ValueError) as ex:
        _LOGGER.error("%s", ex)
        hass.components.persistent_notification.create(
            'Error: {}<br />'
            'You will need to restart hass after fixing.'
            ''.format(ex),
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID)

    if not mygogogate2_list:
        _LOGGER.info("No gates configured")
        return False

    hass.data[DATA_GOGOGATE2] = mygogogate2_list
    return True
