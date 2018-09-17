"""
Support for Gogogate2 garage Doors.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/sensor.gogogate2/
"""
import logging

from homeassistant.const import (CONF_NAME, TEMP_CELSIUS)
from homeassistant.helpers.entity import Entity
from ..gogogate2 import DATA_GOGOGATE2, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


# noinspection PyUnusedLocal
def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Gogogate2 component."""

    name = config.get(CONF_NAME)
    mygogogate2_list = hass.data[DATA_GOGOGATE2]
    mygogogate2 = hass.data[DOMAIN]

    add_entities(MyGogogate2Sensor(
        mygogogate2, door, name) for door in mygogogate2_list)


class MyGogogate2Sensor(Entity):
    """Representation of a Gogogate2 sensor."""

    def __init__(self, mygogogate2, device, name):
        """Initialize with API object, device id."""
        self.mygogogate2 = mygogogate2
        self.device_id = device['door']
        self._name = name or device['name']
        self._status = device['status']
        self._temperature = device['temperature']
        self._available = None

    @property
    def name(self):
        """Return the name of the garage door if any."""
        return self._name if self._name else DEFAULT_NAME

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return 'temperature'

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self._available

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._temperature

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return TEMP_CELSIUS

    def update(self):
        """Update temperature."""
        self._temperature = self._get_temperature(self.device_id)
        self._available = True

    def _get_temperature(self, device_id):
        temperature = None

        try:
            devices = self.mygogogate2.get_devices()
            if devices is False:
                return None

            for device in devices:
                if device['door'] == device_id:
                    temperature = device['temperature']
        except (TypeError, KeyError, NameError, ValueError) as ex:
            _LOGGER.error("%s", ex)

        return temperature
