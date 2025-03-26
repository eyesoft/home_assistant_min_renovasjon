import urllib.parse
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from dateutil.relativedelta import relativedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .data import DataClient

from .const import (
    DOMAIN,
    CONF_STREET_NAME,
    CONF_STREET_CODE,
    CONF_HOUSE_NO,
    CONF_COUNTY_ID,
    CONF_DATE_FORMAT,
    DEFAULT_DATE_FORMAT,
    STARTUP_MESSAGE
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_STREET_NAME): cv.string,
        vol.Required(CONF_STREET_CODE): cv.string,
        vol.Required(CONF_HOUSE_NO): cv.string,
        vol.Required(CONF_COUNTY_ID): cv.string,
        vol.Optional(CONF_DATE_FORMAT, default=DEFAULT_DATE_FORMAT): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: dict):
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["calendar_list"] = None

    street_name = config[DOMAIN][CONF_STREET_NAME]
    street_code = config[DOMAIN][CONF_STREET_CODE]
    house_no = config[DOMAIN][CONF_HOUSE_NO]
    county_id = config[DOMAIN][CONF_COUNTY_ID]
    date_format = config[DOMAIN][CONF_DATE_FORMAT]

    min_renovasjon = MinRenovasjon(hass, street_name, street_code, house_no, county_id, date_format)
    hass.data[DOMAIN]["data"] = min_renovasjon

    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    hass.data[DOMAIN]["calendar_list"] = None
    street_name = config_entry.data.get(CONF_STREET_NAME, "")
    street_code = config_entry.data.get(CONF_STREET_CODE, "")
    house_no = config_entry.data.get(CONF_HOUSE_NO, "")
    county_id = config_entry.data.get(CONF_COUNTY_ID, "")
    date_format = config_entry.options.get(CONF_DATE_FORMAT, DEFAULT_DATE_FORMAT)

    min_renovasjon = MinRenovasjon(hass, street_name, street_code, house_no, county_id, date_format)
    hass.data[DOMAIN]["data"] = min_renovasjon

    await hass.config_entries.async_forward_entry_setups(config_entry, ["sensor", "calendar"])
    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    return True


class MinRenovasjon:
    def __init__(self, hass, gatenavn, gatekode, husnr, kommunenr, date_format):
        self._hass = hass
        self._gatenavn = self._url_encode(gatenavn)
        self._gatekode = gatekode
        self._husnr = husnr
        self._kommunenr = kommunenr
        self._date_format = date_format
        self._data_client = DataClient(hass)

    # Fetches the calender for the specified fractionId
    async def async_get_calender_for_fraction(self, fraction_id):
        calendar_list = await self._async_get_calendar()

        if calendar_list is None:
            return None

        for entry in calendar_list:
            if entry is not None:
                entry_fraction_id, _, _, tommedato_forste, tommedato_neste, _ = entry
                if int(fraction_id) == int(entry_fraction_id):
                    return entry

        return None

    # Fetches the calendar for all fractions
    async def async_get_calendar_list(self):
        return await self._async_get_calendar()

    async def _async_get_calendar(self):
        return await self._data_client.async_get_calendar(
            self._kommunenr,
            self._gatenavn,
            self._gatekode,
            self._husnr
        )

    def format_date(self, date):
        if self._date_format == "None":
            return date
        return date.strftime(self._date_format)

    @staticmethod
    def _url_encode(string):
        string_decoded_encoded = urllib.parse.quote(urllib.parse.unquote(string))
        if string_decoded_encoded != string:
            string = string_decoded_encoded
        return string
