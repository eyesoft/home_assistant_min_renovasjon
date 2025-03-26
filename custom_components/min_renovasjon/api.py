import aiohttp
import asyncio
import json
import logging
import socket

from dateutil.relativedelta import relativedelta
from datetime import date
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import (
    CONST_KOMMUNE_NUMMER,
    CONST_APP_KEY,
    CONST_URL_FRAKSJONER,
    CONST_URL_TOMMEKALENDER,
    CONST_APP_KEY_VALUE,
    NUM_MONTHS,
    APP_CUSTOMERS_URL,
    ADDRESS_LOOKUP_URL
)

_LOGGER = logging.getLogger(__name__)


class ApiClient:

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_get_data(self,
                             kommune_nummer: str,
                             gatenavn: str,
                             gatekode: str,
                             husnummer: str
                             ):

        tommekalender = await self.async_get_tommekalender(kommune_nummer,
                                                           gatenavn,
                                                           gatekode,
                                                           husnummer)

        fraksjoner = await self.async_get_fraksjoner(kommune_nummer)

        return tommekalender, fraksjoner

    async def async_get_tommekalender(self,
                                      kommune_nummer: str,
                                      gatenavn: str,
                                      gatekode: str,
                                      husnummer: str
                                      ):
        headers = {CONST_KOMMUNE_NUMMER: kommune_nummer, CONST_APP_KEY: CONST_APP_KEY_VALUE}

        fra_dato = date.today().strftime("%Y-%m-%d")
        til_dato = (date.today() + relativedelta(months=NUM_MONTHS)).strftime("%Y-%m-%d")

        url = (CONST_URL_TOMMEKALENDER.replace('[gatenavn]', gatenavn)
               .replace('[gatekode]', gatekode)
               .replace('[husnr]', husnummer)
               .replace('[fra_dato]', fra_dato)
               .replace('[til_dato]', til_dato))

        data = await self._client_session_get_data(url, headers)
        return json.loads(data)

    async def async_get_fraksjoner(self, kommune_nummer: str):
        headers = {CONST_KOMMUNE_NUMMER: kommune_nummer, CONST_APP_KEY: CONST_APP_KEY_VALUE}
        url = CONST_URL_FRAKSJONER

        data = await self._client_session_get_data(url, headers)
        return json.loads(data)

    async def async_municipality_is_app_customer(self, kommune_nummer) -> bool:
        customers = None
        url = APP_CUSTOMERS_URL
        params = {"Appid": "MobilOS-NorkartRenovasjon"}

        data = await self._client_session_get_data(url, params=params)
        customers = json.loads(data)

        return any(
            customer["Number"] == kommune_nummer for customer in customers
        )

    async def async_address_lookup(self, search_string):
        url = ADDRESS_LOOKUP_URL
        params = {
            "sok": search_string,
            # Only get the relevant address fields
            "filtrer": "adresser.kommunenummer,"
                       "adresser.adressenavn,"
                       "adresser.adressekode,"
                       "adresser.nummer,"
                       "adresser.kommunenavn,"
                       "adresser.postnummer,"
                       "adresser.poststed",
        }

        data = await self._client_session_get_data(url, params=params)
        return json.loads(data)

    # Sends request to "url" and return data as "UTF-8"
    async def _client_session_get_data(self,
                                       url: str,
                                       headers: dict | None = None,
                                       params: dict | None = None
                                       ):
        try:
            _LOGGER.debug(f"Fetching data from server")

            async with self._session.get(url, params=params, headers=headers) as resp:
                data = await resp.read()

                if resp.ok:
                    return data.decode("UTF-8")
                else:
                    _LOGGER.error("GET returned: %s", resp)
                    return None

        except asyncio.TimeoutError as exception:
            raise ApiException(
                f"Request timeout ({url})"
            ) from exception

        except (KeyError, TypeError) as exception:
            raise ApiException(
                f"Parse error: {exception} ({url})"
            ) from exception

        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise ApiException(
                f"Request error: {exception} ({url})"
            ) from exception

        except Exception as exception:
            raise ApiException(
                f"Exception: {exception} ({url})"
            ) from exception


class ApiException(Exception):
    """Exception"""
