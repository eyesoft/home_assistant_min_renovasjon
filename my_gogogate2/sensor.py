import logging
from homeassistant.const import (TEMP_CELSIUS)
from homeassistant.helpers.entity import Entity
from ..my_gogogate2 import (DATA_GOGOGATE2, DEFAULT_NAME)

_LOGGER = logging.getLogger(__name__)


# noinspection PyUnusedLocal,PyUnresolvedReferences,PyPep8Naming
async def async_setup_platform(hass, config, async_add_entites, discovery_info=None):
    """Set up the Gogogate2 component."""
    gogogate2 = hass.data[DATA_GOGOGATE2].gogogate2
    name = hass.data[DATA_GOGOGATE2].name

    devices = gogogate2.get_devices()
    if devices is False:
        raise ValueError(
            "Username or Password is incorrect or no devices found")

    async_add_entites(Gogogate2Sensor(
        gogogate2, door, name) for door in devices)


class Gogogate2Sensor(Entity):
    """Representation of a Gogogate2 sensor."""

    def __init__(self, gogogate2, device, name):
        """Initialize with API object, device id."""
        self.gogogate2 = gogogate2
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
        try:
            devices = self.gogogate2.get_devices()
            self._available = True
            if devices is False:
                raise ValueError(
                    "Username or Password is incorrect or no devices found")

            for device in devices:
                if device['door'] == self.device_id:
                    self._temperature = device['temperature']
        except (TypeError, KeyError, NameError, ValueError) as ex:
            _LOGGER.error("%s", ex)
            self._available = False
