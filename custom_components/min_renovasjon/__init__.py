import aiohttp
import asyncio
import urllib.parse
import requests
import json
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from datetime import date
from datetime import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import (
    DOMAIN,
    CONF_STREET_NAME,
    CONF_STREET_CODE,
    CONF_HOUSE_NO,
    CONF_COUNTY_ID,
    CONF_DATE_FORMAT,
    DEFAULT_DATE_FORMAT,
    CONST_KOMMUNE_NUMMER,
    CONST_APP_KEY,
    CONST_URL_FRAKSJONER,
    CONST_URL_TOMMEKALENDER,
    CONST_APP_KEY_VALUE
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
    #date_format = config[DOMAIN][CONF_DATE_FORMAT]
    date_format = None
    min_renovasjon = MinRenovasjon(hass, street_name, street_code, house_no, county_id, date_format)

    hass.data[DOMAIN]["data"] = min_renovasjon

    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["calendar_list"] = None
    street_name = config_entry.data.get(CONF_STREET_NAME, "")
    street_code = config_entry.data.get(CONF_STREET_CODE, "")
    house_no = config_entry.data.get(CONF_HOUSE_NO, "")
    county_id = config_entry.data.get(CONF_COUNTY_ID, "")
    #date_format = config_entry.data.get(CONF_DATE_FORMAT, "")
    date_format = None
    min_renovasjon = MinRenovasjon(hass, street_name, street_code, house_no, county_id, date_format)

    hass.data[DOMAIN]["data"] = min_renovasjon
    hass.config_entries.async_setup_platforms(config_entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    return True

class MinRenovasjon:
    def __init__(self, hass, gatenavn, gatekode, husnr, kommunenr, date_format):
        self._hass = hass
        self.gatenavn = self._url_encode(gatenavn)
        self.gatekode = gatekode
        self.husnr = husnr
        self._kommunenr = kommunenr
        #self._date_format = date_format

    @staticmethod
    def _url_encode(string):
        string_decoded_encoded = urllib.parse.quote(urllib.parse.unquote(string))
        if string_decoded_encoded != string:
            string = string_decoded_encoded
        return string

    async def _get_tommekalender_from_web_api(self):
        _LOGGER.debug("_get_tommekalender_from_web_api")
    
        header = {CONST_KOMMUNE_NUMMER: self._kommunenr, CONST_APP_KEY: CONST_APP_KEY_VALUE}
        url = CONST_URL_TOMMEKALENDER
        url = url.replace('[gatenavn]', self.gatenavn)
        url = url.replace('[gatekode]', self.gatekode)
        url = url.replace('[husnr]', self.husnr)

        async with aiohttp.ClientSession(headers=header) as session:
            async with session.get(url) as resp:
                data = await resp.read()

                if resp.ok:
                    return data.decode("UTF-8")
                else:
                    _LOGGER.error("GET Tommekalender returned: %s", resp)
                    return None

    async def _get_fraksjoner_from_web_api(self):
        _LOGGER.debug("_get_fraksjoner_from_web_api")
    
        header = {CONST_KOMMUNE_NUMMER: self._kommunenr, CONST_APP_KEY: CONST_APP_KEY_VALUE}
        url = CONST_URL_FRAKSJONER

        async with aiohttp.ClientSession(headers=header) as session:
            async with session.get(url) as resp:
                data = await resp.read()

                if resp.ok:
                    return data.decode("UTF-8")
                else:
                    _LOGGER.error("GET Fraksjoner returned: %s", resp)
                    return None

    async def _get_from_web_api(self):
        tommekalender = await self._get_tommekalender_from_web_api()
        fraksjoner = await self._get_fraksjoner_from_web_api()
        return tommekalender, fraksjoner

    async def _get_calendar_list(self, refresh=False):
        data = self._hass.data[DOMAIN]["calendar_list"]
        
        if refresh or data is None:
            tommekalender, fraksjoner = await self._get_from_web_api()
            kalender_list = self._parse_calendar_list(tommekalender, fraksjoner)
        else:
            kalender_list = data

        if kalender_list is None:
            return None

        check_for_refresh = False
        if not refresh:
            check_for_refresh = self._check_for_refresh_of_data(kalender_list)

        if check_for_refresh:
            kalender_list = await self._get_calendar_list(refresh=True)

        self._hass.data[DOMAIN]["calendar_list"] = kalender_list
        
        return kalender_list

    @staticmethod
    def _parse_calendar_list(tommekalender, fraksjoner):
        kalender_list = []

        if tommekalender is None or fraksjoner is None:
            _LOGGER.error("Could not fetch calendar. Check configuration parameters.")
            return None

        tommekalender_json = json.loads(tommekalender)
        fraksjoner_json = json.loads(fraksjoner)

        for calender_entry in tommekalender_json:
            fraksjon_id = calender_entry['FraksjonId']
            tommedato_forste = None
            tommedato_neste = None

            if len(calender_entry['Tommedatoer']) == 1:
                tommedato_forste = calender_entry['Tommedatoer'][0]
            else:
                tommedato_forste, tommedato_neste = calender_entry['Tommedatoer']

            if tommedato_forste is not None:
                tommedato_forste = datetime.strptime(tommedato_forste, "%Y-%m-%dT%H:%M:%S")
            if tommedato_neste is not None:
                tommedato_neste = datetime.strptime(tommedato_neste, "%Y-%m-%dT%H:%M:%S")

            for fraksjon in fraksjoner_json:
                if int(fraksjon['Id']) == int(fraksjon_id):
                    fraksjon_navn = fraksjon['Navn']
                    fraksjon_ikon = fraksjon['Ikon']

                    kalender_list.append((fraksjon_id, fraksjon_navn, fraksjon_ikon, tommedato_forste, tommedato_neste))
                    continue

        return kalender_list

    @staticmethod
    def _check_for_refresh_of_data(kalender_list):
        if kalender_list is None:
            _LOGGER.debug("Calendar is empty, forcing refresh")
            return True

        for entry in kalender_list:
            _, _, _, tommedato_forste, tommedato_neste = entry

            if tommedato_forste is None or tommedato_neste is None:
                _LOGGER.debug("Data needs refresh")
                return True

            if tommedato_forste.date() < date.today() or tommedato_neste.date() < date.today():
                _LOGGER.debug("Data needs refresh")
                return True

        return False

    async def get_calender_for_fraction(self, fraksjon_id):
        calendar_list = self._hass.data[DOMAIN]["calendar_list"]
    
        if calendar_list is None:
            calendar_list = await self._get_calendar_list()
            self._hass.data[DOMAIN]["calendar_list"] = calendar_list
        
        for entry in calendar_list:
            entry_fraksjon_id, _, _, _, _= entry
            if int(fraksjon_id) == int(entry_fraksjon_id):
                return entry

    @property
    def calender_list(self):
        return self._hass.data[DOMAIN]["calendar_list"]

    def format_date(self, date):
        return date
        #if self._date_format == "None":
        #    return date
        #return date.strftime(self._date_format)
