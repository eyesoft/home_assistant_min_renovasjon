import requests
import json
from datetime import date
from datetime import datetime
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

DOMAIN = "min_renovasjon"
DATA_MIN_RENOVASJON = "data_min_renovasjon"

CONF_STREET_NAME = "street_name"
CONF_STREET_CODE = "street_code"
CONF_HOUSE_NO = "house_no"
CONF_COUNTY_ID = "county_id"
CONF_DATE_FORMAT = "date_format"
DEFAULT_DATE_FORMAT = "%d/%m/%Y"

CONST_KOMMUNE_NUMMER = "Kommunenr"
CONST_APP_KEY = "RenovasjonAppKey"
CONST_URL_FRAKSJONER = 'https://komteksky.norkart.no/komtek.renovasjonwebapi/api/fraksjoner'
CONST_URL_TOMMEKALENDER = 'https://komteksky.norkart.no/komtek.renovasjonwebapi/api/tommekalender?' \
                          'gatenavn=[gatenavn]&gatekode=[gatekode]&husnr=[husnr]'
CONST_DATA_FILENAME = "min_renovasjon.dat"
CONST_DATA_HEADER_COMMENT = '# Auto-generated file. Do not edit.'
CONST_APP_KEY_VALUE = "AE13DEEC-804F-4615-A74E-B4FAC11F0A30"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_STREET_NAME): cv.string,
        vol.Required(CONF_STREET_CODE): cv.string,
        vol.Required(CONF_HOUSE_NO): cv.string,
        vol.Required(CONF_COUNTY_ID): cv.string,
        vol.Optional(CONF_DATE_FORMAT, default=DEFAULT_DATE_FORMAT): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    """Set up the MinRenovasjon component."""
    street_name = config[DOMAIN][CONF_STREET_NAME]
    street_code = config[DOMAIN][CONF_STREET_CODE]
    house_no = config[DOMAIN][CONF_HOUSE_NO]
    county_id = config[DOMAIN][CONF_COUNTY_ID]
    date_format = config[DOMAIN][CONF_DATE_FORMAT]

    min_renovasjon = MinRenovasjon(street_name, street_code, house_no, county_id, date_format)
    hass.data[DATA_MIN_RENOVASJON] = min_renovasjon

    return True


class MinRenovasjon:
    def __init__(self, gatenavn, gatekode, husnr, kommunenr, date_format):
        self.gatenavn = gatenavn
        self.gatekode = gatekode
        self.husnr = husnr
        self._kommunenr = kommunenr
        self._date_format = date_format
        self._kalender_list = self._get_calendar_list()

    def refresh_calendar(self):
        do_refresh = self._check_for_refresh_of_data(self._kalender_list)
        if do_refresh:
            self._kalender_list = self._get_calendar_list()

    def _get_tommekalender_from_web_api(self):
        header = {CONST_KOMMUNE_NUMMER: self._kommunenr, CONST_APP_KEY: CONST_APP_KEY_VALUE}

        url = CONST_URL_TOMMEKALENDER
        url = url.replace('[gatenavn]', self.gatenavn)
        url = url.replace('[gatekode]', self.gatekode)
        url = url.replace('[husnr]', self.husnr)

        response = requests.get(url, headers=header)
        if response.status_code == requests.codes.ok:
            data = response.text
            return data
        else:
            _LOGGER.error(response.status_code)
            return None

    def _get_fraksjoner_from_web_api(self):
        header = {CONST_KOMMUNE_NUMMER: self._kommunenr, CONST_APP_KEY: CONST_APP_KEY_VALUE}
        url = CONST_URL_FRAKSJONER

        response = requests.get(url, headers=header)
        if response.status_code == requests.codes.ok:
            data = response.text
            return data
        else:
            _LOGGER.error(response.status_code)
            return None

    @staticmethod
    def _read_from_file():
        try:
            _LOGGER.debug("Reading content from file")

            file = open(CONST_DATA_FILENAME)
            lines = file.readlines()
            tommekalender = lines[1]
            fraksjoner = lines[2]
            file.close()

            return tuple((tommekalender, fraksjoner))
        except FileNotFoundError:
            _LOGGER.debug("File not found")
            return None

    @staticmethod
    def _write_to_file(tommekalender, fraksjoner):
        _LOGGER.debug("Writing content to file")

        file = open(CONST_DATA_FILENAME, "w")
        file.write("{}\n".format(CONST_DATA_HEADER_COMMENT))
        file.write("{}\n".format(tommekalender))
        file.write("{}\n".format(fraksjoner))
        file.close()

    def _get_from_web_api(self):
        tommekalender = self._get_tommekalender_from_web_api()
        fraksjoner = self._get_fraksjoner_from_web_api()

        if fraksjoner is not None and tommekalender is not None:
            self._write_to_file(tommekalender, fraksjoner)

        return tommekalender, fraksjoner

    def _get_calendar_list(self, refresh=False):
        data = None

        if not refresh:
            data = self._read_from_file()

        if refresh or data is None:
            _LOGGER.debug("Refresh or no data. Fetching from API.")
            tommekalender, fraksjoner = self._get_from_web_api()
        else:
            tommekalender, fraksjoner = data

        kalender_list = self._parse_calendar_list(tommekalender, fraksjoner)

        check_for_refresh = False
        if not refresh:
            check_for_refresh = self._check_for_refresh_of_data(kalender_list)

        if check_for_refresh:
            _LOGGER.debug("Refreshing data...")
            kalender_list = self._get_calendar_list(refresh=True)

        _LOGGER.debug("Returning calendar list")
        return kalender_list

    @staticmethod
    def _parse_calendar_list(tommekalender, fraksjoner):
        kalender_list = []

        tommekalender_json = json.loads(tommekalender)
        fraksjoner_json = json.loads(fraksjoner)

        for calender_entry in tommekalender_json:
            fraksjon_id = calender_entry['FraksjonId']

            tommedato_forste, tommedato_neste = calender_entry['Tommedatoer']

            tommedato_forste = datetime.strptime(tommedato_forste, "%Y-%m-%dT%H:%M:%S")
            tommedato_neste = datetime.strptime(tommedato_neste, "%Y-%m-%dT%H:%M:%S")

            for fraksjon in fraksjoner_json:
                if fraksjon['Id'] == fraksjon_id:
                    fraksjon_navn = fraksjon['Navn']
                    fraksjon_ikon = fraksjon['Ikon']

                    kalender_list.append((fraksjon_id, fraksjon_navn, fraksjon_ikon, tommedato_forste, tommedato_neste))
                    continue

        return kalender_list

    @staticmethod
    def _check_for_refresh_of_data(kalender_list):
        _LOGGER.debug("Checking if data needs refresh")

        for entry in kalender_list:
            _, _, _, tommedato_forste, tommedato_neste = entry

            if tommedato_forste.date() < date.today() or tommedato_neste.date() < date.today():
                _LOGGER.debug("Data need refresh")
                return True

        return False

    def get_calender_for_fraction(self, fraksjon_id):
        for entry in self._kalender_list:
            entry_fraksjon_id, _, _, _, _= entry
            if fraksjon_id == entry_fraksjon_id:
                return entry

    @property
    def calender_list(self):
        return self._kalender_list

    def format_date(self, date):
        return date.strftime(self._date_format)
