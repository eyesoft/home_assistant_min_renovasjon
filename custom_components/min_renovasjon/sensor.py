import logging

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from ..min_renovasjon import DATA_MIN_RENOVASJON
from datetime import date

_LOGGER = logging.getLogger(__name__)

CONF_FRACTION_ID = "fraction_id"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_FRACTION_ID): vol.All(cv.ensure_list),
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    fraction_ids = config.get(CONF_FRACTION_ID)
    min_renovasjon = hass.data[DATA_MIN_RENOVASJON]

    add_entities(MinRenovasjonSensor(min_renovasjon, fraction_id) for fraction_id in fraction_ids)


class MinRenovasjonSensor(Entity):

    def __init__(self, min_renovasjon, fraction_id):
        """Initialize with API object, device id."""
        self._min_renovasjon = min_renovasjon
        self._fraction_id = fraction_id
        self._available = True
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the fraction if any."""
        fraction = self._min_renovasjon.get_calender_for_fraction(self._fraction_id)
        if fraction is not None:
            return fraction[1]

    @property
    def device_class(self):
        """Return the class of this device."""
        return "date"

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self._available

    @property
    def state(self):
        """Return the state/date of the fraction."""
        fraction = self._min_renovasjon.get_calender_for_fraction(self._fraction_id)
        if fraction is not None:
            return fraction[3]

    @property
    def entity_picture(self):
        """Return entity specific state attributes."""
        path = "/local/min_renovasjon/"
        return "{0}{1}.png".format(path, self._fraction_id)

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return self._attributes

    def update(self):
        """Update calendar."""
        self._min_renovasjon.refresh_calendar()

        fraction = self._min_renovasjon.get_calender_for_fraction(self._fraction_id)
        if fraction is not None:
            if fraction[3] is not None:
                pickupDate = fraction[3].date()
                today = date.today()
                diff = pickupDate - today
                self._attributes['days_to_pickup'] = diff.days
                self._attributes['formatted_date'] = self._min_renovasjon.format_date(fraction[3])
                self._attributes['date_next_pickup'] = fraction[4]
                self._attributes['fraction_id'] = self._fraction_id
                self._attributes['fraction_name'] = fraction[1]
                self._attributes['fraction_icon'] = fraction[2]
