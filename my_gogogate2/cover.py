import logging
from homeassistant.components.cover import (CoverDevice, SUPPORT_OPEN, SUPPORT_CLOSE)
from homeassistant.const import (STATE_CLOSED)
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

    async_add_entites(Gogogate2Cover(
        gogogate2, door, name) for door in devices)


class Gogogate2Cover(CoverDevice):
    """Representation of a Gogogate2 cover."""

    def __init__(self, gogogate2, device, name):
        """Initialize with API object, device id."""
        self.gogogate2 = gogogate2
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
        self.gogogate2.close_device(self.device_id)

    def open_cover(self, **kwargs):
        """Issue open command to cover."""
        self.gogogate2.open_device(self.device_id)

    def update(self):
        """Update status of cover."""
        try:
            self._status = self.gogogate2.get_status(self.device_id)
            self._available = True
        except (TypeError, KeyError, NameError, ValueError) as ex:
            _LOGGER.error("%s", ex)
            self._status = None
            self._available = False
