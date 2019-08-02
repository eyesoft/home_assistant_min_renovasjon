import logging
import voluptuous as vol
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_IP_ADDRESS, CONF_NAME)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['pygogogate2==0.1.1']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'my_gogogate2'
DOMAIN = "my_gogogate2"
DATA_GOGOGATE2 = "data_my_gogogate2"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    hass.data[DATA_GOGOGATE2] = Gogogate2Module(hass, config)
    return True


class Gogogate2Module:
    def __init__(self, hass, config):
        """Initialize of Buspro module."""
        self.hass = hass
        self.config = config
        self.gogogate2 = None
        self.name = None

        from pygogogate2 import Gogogate2API as pygogogate2

        ip_address = config[DOMAIN][CONF_IP_ADDRESS]
        username = config[DOMAIN][CONF_USERNAME]
        password = config[DOMAIN][CONF_PASSWORD]
        name = config[DOMAIN][CONF_NAME]
        self.name = name

        self.gogogate2 = pygogogate2(username, password, ip_address)
