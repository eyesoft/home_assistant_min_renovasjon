"""
Support for Gogogate2 garage Doors.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/cover.gogogate2/
"""
import logging

from homeassistant.components.cover import (CoverDevice, SUPPORT_OPEN, SUPPORT_CLOSE)
from homeassistant.const import (STATE_CLOSED, CONF_NAME)
from ..gogogate2 import DATA_GOGOGATE2, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


# noinspection PyUnusedLocal
def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Gogogate2 component."""

    name = config.get(CONF_NAME)
    mygogogate2_list = hass.data[DATA_GOGOGATE2]
    mygogogate2 = hass.data[DOMAIN]

    add_entities(MyGogogate2Cover(
        mygogogate2, door, name) for door in mygogogate2_list)


class MyGogogate2Cover(CoverDevice):
    """Representation of a Gogogate2 cover."""

    def __init__(self, mygogogate2, device, name):
        """Initialize with API object, device id."""
        self.mygogogate2 = mygogogate2
        self.device_id = device['door']
        self._name = name or device['name']
        self._status = device['status']
        self._available = None

    @property
    def name(self):
        """Return the name of the garage door if any."""
        return self._name if self._name else DEFAULT_NAME

    @property
    def is_closed(self):
        """Return true if cover is closed, else False."""
        return self._status == STATE_CLOSED

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return 'garage'

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_OPEN | SUPPORT_CLOSE

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self._available

    def close_cover(self, **kwargs):
        """Issue close command to cover."""
        self.mygogogate2.close_device(self.device_id)

    def open_cover(self, **kwargs):
        """Issue open command to cover."""
        self.mygogogate2.open_device(self.device_id)

    def update(self):
        """Update status of cover."""
        try:
            self._status = self.mygogogate2.get_status(self.device_id)
            self._available = True
        except (TypeError, KeyError, NameError, ValueError) as ex:
            _LOGGER.error("%s", ex)
            self._status = None
            self._available = False
