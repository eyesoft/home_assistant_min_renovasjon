import aiohttp
import re
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from typing import Dict, List, Tuple
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from dateutil.relativedelta import relativedelta
from .api import ApiClient, ApiException

from .const import (
    DOMAIN,
    CONF_STREET_NAME,
    CONF_STREET_CODE,
    CONF_HOUSE_NO,
    CONF_COUNTY_ID,
    CONF_DATE_FORMAT,
    DEFAULT_DATE_FORMAT,
    CONF_FRACTION_IDS
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        address = None

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            try:
                address = user_input["address"]
                error, address_info, title = await self._get_address_info(address)

                if error is not None:
                    errors["base"] = error

                if address_info is not None:
                    return self.async_create_entry(title=title, data=address_info)

            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # errors substitution in language file
        return self.async_show_form(
            step_id="user",

            data_schema=vol.Schema({
                vol.Required("address", default=address): str
            }),
            errors=errors
        )

    async def _get_address_info(self, address_search_string):
        error, address_info = await self._async_address_lookup(address_search_string)

        if error is not None:
            return error, None, None

        if address_info is not None:
            (
                self.street,
                self.street_code,
                self.number,
                self.municipality,
                self.municipality_code,
                self.postal_code,
                self.postal,
            ) = address_info

        if await self.municipality_is_app_customer:
            text = "self.fractions = self._get_fractions()"
        else:
            return "municipality_not_customer", None, None

        address = {
            "street_name": self.street,
            "street_code": str(self.street_code),
            "house_no": str(self.number),
            "county_id": str(self.municipality_code)
        }

        title = f"{self.street} {self.number}, {self.postal_code} {self.postal}"

        return None, address, title

    async def _async_address_lookup(self, s: str) -> Tuple:
        """
        Makes an API call to geonorge.no, the official resource for open geo data in Norway.
        This function is used to get deterministic address properties that is needed for
        further API calls with regards to Min Renovasjon, mainly municipality, municipality code,
        street name and street code.
        :param s: Search string for which address to search
        :return: Tuple of address fields
        """
        error = None
        data = None

        regex = r"(.*ve)(i|g)(.*)"
        subst = "\\1*\\3"
        search_string = re.sub(regex, subst, s, 0, re.MULTILINE)

        session = async_get_clientsession(self.hass)
        client = ApiClient(session)
        data = await client.async_address_lookup(search_string)

        if data is None:
            return "no_address_found", None

        if not data["adresser"]:
            return "no_address_found", None

        if len(data["adresser"]) > 1:
            return "multiple_addresses_found", None

        return None, (
            data["adresser"][0]["adressenavn"],
            data["adresser"][0]["adressekode"],
            data["adresser"][0]["nummer"],
            data["adresser"][0]["kommunenavn"],
            data["adresser"][0]["kommunenummer"],
            data["adresser"][0]["postnummer"],
            data["adresser"][0]["poststed"],
        )

    @property
    async def municipality_is_app_customer(self) -> bool:
        """
        Make an API call to get all customers of the NorkartRenovasjon service which
        supports the Min Renovasjon app. Then check if this municipality is actually
        a customer or not.
        :return: Boolean indicating if this municipality is a customer or not.
        """
        session = async_get_clientsession(self.hass)
        client = ApiClient(session)
        return await client.async_municipality_is_app_customer(self.municipality_code)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return MinRenovasjonFlowHandler()


class MinRenovasjonFlowHandler(config_entries.OptionsFlow):
    """Options flow handler."""

    @property
    def config_entry(self):
        return self.hass.config_entries.async_get_entry(self.handler)

    async def async_step_init(self, user_input=None):
        """Manage the options."""

        if user_input is not None:
            if "date_format" not in user_input:
                user_input["date_format"] = "None"

            return self.async_create_entry(title=DOMAIN, data=user_input)

        options = self.config_entry.options
        fraction_ids = options.get(CONF_FRACTION_IDS, [])
        date_format = options.get(CONF_DATE_FORMAT, DEFAULT_DATE_FORMAT)

        municipality_code = self.config_entry.data.get(CONF_COUNTY_ID, "")
        street_name = self.config_entry.data.get(CONF_STREET_NAME, "")
        street_code = self.config_entry.data.get(CONF_STREET_CODE, "")
        house_no = self.config_entry.data.get(CONF_HOUSE_NO, "")

        fraction_list = await self._get_fractions(municipality_code)
        calendar = await self._get_calendar(municipality_code, street_name, street_code, house_no)
        fractions = {}

        for fraction in fraction_list:
            if calendar is not None:
                if [item for item in calendar if item["FraksjonId"] == fraction["Id"]]:
                    fractions[str(fraction["Id"])] = fraction["Navn"]
            else:
                fractions[str(fraction["Id"])] = fraction["Navn"]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FRACTION_IDS, default=fraction_ids): cv.multi_select(fractions),
                    vol.Optional(CONF_DATE_FORMAT, description={"suggested_value": date_format}): cv.string
                }
            )
        )

    async def _get_fractions(self, kommune_nummer) -> Dict:
        session = async_get_clientsession(self.hass)
        client = ApiClient(session)
        return await client.async_get_fraksjoner(kommune_nummer)

    async def _get_calendar(self, municipality_code, street_name, street_code, house_no) -> Dict:
        session = async_get_clientsession(self.hass)
        client = ApiClient(session)
        return await client.async_get_tommekalender(municipality_code,
                                                    street_name,
                                                    street_code,
                                                    house_no)
