"""
Support for Gogogate2 garage Doors.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/binary_sensor.my_gogogate2/
"""
import logging

from homeassistant.components.binary_sensor import (BinarySensorDevice)
from homeassistant.const import (CONF_NAME)
from ..gogogate2 import DATA_GOGOGATE2, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


# noinspection PyUnusedLocal
def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Gogogate2 component."""

    name = config.get(CONF_NAME)
    mygogogate2_list = hass.data[DATA_GOGOGATE2]
    mygogogate2 = hass.data[DOMAIN]

    add_entities(MyGogogate2BinarySensor(
        mygogogate2, door, name) for door in mygogogate2_list)


class MyGogogate2BinarySensor(BinarySensorDevice):
    """Representation of a Gogogate2 binary sensor."""

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
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return 'garage_door'

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self._available

    @property
    def is_on(self):
        if self._status == "closed":
            return False
        else:
            return True

    def update(self):
        """Update status."""
        self._status = self.mygogogate2.get_status(self.device_id)
        self._available = True
