import aiohttp
import asyncio
import json

from collections import namedtuple
from typing import Dict, List, Tuple
import requests
import re

import logging
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_STREET_NAME,
    CONF_STREET_CODE,
    CONF_HOUSE_NO,
    CONF_COUNTY_ID,
    CONF_DATE_FORMAT,
    DEFAULT_DATE_FORMAT,
    CONF_FRACTION_IDS,
    ADDRESS_LOOKUP_URL,
    APP_CUSTOMERS_URL,
    CONST_APP_KEY_VALUE,
    KOMTEK_API_BASE_URL,
    CONST_URL_FRAKSJONER
)

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        address = None
        
        if user_input is not None:
            try:
                address = user_input["address"]
                error, address_info = await self._get_address_info(address)
                
                if error is not None:
                    errors["base"] = error
                
                if address_info is not None:
                    return self.async_create_entry(title="Min Renovasjon", data=address_info)
                    
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        #errors substitution in language file
        return self.async_show_form(
            step_id="user",

            data_schema=vol.Schema({
            	vol.Required("address", default=address): str
            }),
            errors=errors
        )

    async def _get_address_info(self, address_search_string):
        error, address_info = await self._address_lookup(address_search_string)

        if error is not None:
            return error, None

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
            return "municipality_not_customer", None
       
        address = {
            "street_name": self.street,
            "street_code": str(self.street_code),
            "house_no": str(self.number),
            "county_id": str(self.municipality_code)
        }        
        
        return None, address

    async def _address_lookup(self, s: str) -> Tuple:
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

        params={
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
           
        async with aiohttp.ClientSession() as session:
            async with session.get(url=ADDRESS_LOOKUP_URL, params=params) as resp:
                response = await resp.read()
                if resp.ok:
                    data = json.loads(response.decode("UTF-8"))
        
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
        customers = None
       
        async with aiohttp.ClientSession() as session:
            async with session.get(url=APP_CUSTOMERS_URL, params={"Appid": "MobilOS-NorkartRenovasjon"}) as resp:
                response = await resp.read()
                if resp.ok:
                    customers = json.loads(response.decode("UTF-8"))
        
        return any(
            customer["Number"] == self.municipality_code for customer in customers
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return OptionsFlowHandler(config_entry)
        
class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow handler."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Manage the options."""

        if user_input is not None:
            self.options.update(user_input)
            return self.async_create_entry(title=DOMAIN, data=self.options)

        options = self.config_entry.options
        fraction_ids = options.get(CONF_FRACTION_IDS, [])
        
        municipality_code = self.config_entry.data.get(CONF_COUNTY_ID, "")
        fraction_list = await self._get_fractions(municipality_code)
        fractions = {}
        
        for fraction in fraction_list:
            fractions[str(fraction["Id"])] = fraction["Navn"]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FRACTION_IDS, default=fraction_ids): cv.multi_select(fractions)
                }
            )
        )

    async def _get_fractions(self, municipality_code) -> Dict:
        headers = {"RenovasjonAppKey": CONST_APP_KEY_VALUE, "Kommunenr": municipality_code}
        params = {"server": CONST_URL_FRAKSJONER}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url=KOMTEK_API_BASE_URL, params=params) as resp:
                response = await resp.read()
                if resp.ok:
                    return json.loads(response.decode("UTF-8"))

        return None

