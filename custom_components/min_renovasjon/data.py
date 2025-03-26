import aiohttp
import logging

from dateutil.relativedelta import relativedelta
from datetime import date
from datetime import datetime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import (DOMAIN)
from .api import ApiClient, ApiException

_LOGGER = logging.getLogger(__name__)


class DataClient:

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    # Reads the calendar from Min Renovasjon and handles caching
    async def async_get_calendar(self,
        kommune_nummer: str,
        gatenavn: str,
        gatekode: str,
        husnummer: str
    ) -> dict:

        calendar_list = self._hass.data[DOMAIN]["calendar_list"]
        calendar_needs_refresh = self._check_for_refresh_of_data(calendar_list)

        if calendar_needs_refresh:
            session = async_get_clientsession(self._hass)
            client = ApiClient(session)

            tommekalender, fraksjoner = await client.async_get_data(
                kommune_nummer,
                gatenavn,
                gatekode,
                husnummer
            )

            calendar_list = self._parse_calendar_list(tommekalender, fraksjoner)
            self._hass.data[DOMAIN]["calendar_list"] = calendar_list

        return calendar_list

    # Parses Tømmekalender and Fraksjoner and returns a combined calendar list
    @staticmethod
    def _parse_calendar_list(tommekalender, fraksjoner):
        calendar_list = []

        if tommekalender is None or fraksjoner is None:
            _LOGGER.error("Could not fetch calendar. Check configuration parameters.")
            return None

        for calender_entry in tommekalender:
            fraksjon_id = calender_entry['FraksjonId']
            tommedato_forste = None
            tommedato_neste = None
            tommedato_alle = None

            if len(calender_entry['Tommedatoer']) == 1:
                tommedato_forste = calender_entry['Tommedatoer'][0]
            else:
                tommedato_forste = calender_entry['Tommedatoer'][0]
                tommedato_neste = calender_entry['Tommedatoer'][1]

            tommedato_alle = calender_entry['Tommedatoer']

            if tommedato_forste is not None:
                tommedato_forste = datetime.strptime(tommedato_forste, "%Y-%m-%dT%H:%M:%S")
            if tommedato_neste is not None:
                tommedato_neste = datetime.strptime(tommedato_neste, "%Y-%m-%dT%H:%M:%S")

            for fraksjon in fraksjoner:
                if int(fraksjon['Id']) == int(fraksjon_id):
                    fraksjon_navn = fraksjon['Navn']

                    fraksjon_ikon = fraksjon['NorkartStandardFraksjonIkon']
                    if fraksjon_ikon is None:
                        fraksjon_ikon = fraksjon['Ikon']
                        fraksjon_ikon = fraksjon_ikon.replace("http:", "https:")

                    calendar_list.append((fraksjon_id,
                                            fraksjon_navn,
                                            fraksjon_ikon,
                                            tommedato_forste,
                                            tommedato_neste,
                                            tommedato_alle))
                    continue

        return calendar_list

    # Checks if calendar data needs to be updated
    @staticmethod
    def _check_for_refresh_of_data(calendar_list):

        if calendar_list is None:
            _LOGGER.debug("Calendar is empty. Data needs to be read.")
            return True

        for entry in calendar_list:
            _, _, _, tommedato_forste, tommedato_neste, _ = entry

            if tommedato_forste is None or tommedato_forste.date() < date.today() or (
                    tommedato_neste is not None and tommedato_neste.date() < date.today()):
                _LOGGER.debug("Date out of range. Data need to be read.")
                return True

        return False

