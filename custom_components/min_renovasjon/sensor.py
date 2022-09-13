import logging
import json
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from homeassistant.helpers.restore_state import RestoreEntity 
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from datetime import date
from datetime import timedelta
from .const import (
    DOMAIN,
    CONF_FRACTION_IDS,
    CONF_FRACTION_ID
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(hours=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_FRACTION_ID): vol.All(cv.ensure_list),
})

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    min_renovasjon = hass.data[DOMAIN]["data"]
    calendar_list = await min_renovasjon._get_calendar_list()
    fraction_ids = config.get(CONF_FRACTION_ID)

    add_entities(MinRenovasjonSensor(min_renovasjon, fraction_id, calendar_list) for fraction_id in fraction_ids)

async def async_setup_entry(hass, config_entry, async_add_entities):
    min_renovasjon = hass.data[DOMAIN]["data"]
    calendar_list = await min_renovasjon._get_calendar_list()
    entities = []
    fraction_ids = config_entry.options.get(CONF_FRACTION_IDS, [])
    
    for fraction_id in fraction_ids:
        entities.append(MinRenovasjonSensor(min_renovasjon, fraction_id, calendar_list))
        
    async_add_entities(entities)

class MinRenovasjonSensor(Entity):

    def __init__(self, min_renovasjon, fraction_id, calendar_list):
        """Initialize with API object, device id."""
        self._state = None
        self._calendar_list = calendar_list
        self._min_renovasjon = min_renovasjon
        self._fraction_id = int(fraction_id)
        self._available = True
        self._attributes = {}
        self._attr_unique_id = self.get_name()
        
    @property
    def should_poll(self):
        return True

    @property
    def device_class(self):
        """Return the class of this device."""
        return "date"

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self._available

    @property
    def entity_picture(self):
        """Return entity specific state attributes."""
        path = "/local/min_renovasjon/"
        return "{0}{1}.png".format(path, self._fraction_id)
      
    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return self._attributes
          
    @property
    def name(self):
        """Return the name."""
        return self.get_name()

    def get_name(self):
        if self._calendar_list is not None:
            for fraction in self._calendar_list:
                if int(fraction[0]) == self._fraction_id:
                    return fraction[1]
        return None

    @property
    def state(self):
        """Return the state/date of the fraction."""
        return self._state

    async def async_update(self):
        """Update calendar."""
        
        fraction = await self._min_renovasjon.get_calender_for_fraction(self._fraction_id)

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
                
                self._state = fraction[3]
                
    async def async_added_to_hass(self):
        await self.async_update()

