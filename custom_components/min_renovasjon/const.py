VERSION = "2.6.1"
NAME = "Min Renovasjon"
ISSUE_URL = "https://github.com/eyesoft/home_assistant_min_renovasjon/issues"
DOMAIN = "min_renovasjon"
CONF_STREET_NAME = "street_name"
CONF_STREET_CODE = "street_code"
CONF_HOUSE_NO = "house_no"
CONF_COUNTY_ID = "county_id"
CONF_DATE_FORMAT = "date_format"
DEFAULT_DATE_FORMAT = "%d/%m/%Y"
CONST_KOMMUNE_NUMMER = "Kommunenr"
CONST_APP_KEY = "RenovasjonAppKey"
CONST_APP_KEY_VALUE = "AE13DEEC-804F-4615-A74E-B4FAC11F0A30"
CONF_FRACTION_IDS = "fraction_ids"
CONF_FRACTION_ID = "fraction_id"
ADDRESS_LOOKUP_URL = "https://ws.geonorge.no/adresser/v1/sok?"
APP_CUSTOMERS_URL = "https://www.webatlas.no/wacloud/servicerepository/CatalogueService.svc/json/GetRegisteredAppCustomers"
KOMTEK_API_BASE_URL = "https://norkartrenovasjon.azurewebsites.net/proxyserver.ashx"
CONST_URL_FRAKSJONER = KOMTEK_API_BASE_URL + "?server=https://komteksky.norkart.no/MinRenovasjon.Api/api/fraksjoner"
CONST_URL_TOMMEKALENDER = KOMTEK_API_BASE_URL + "?server=https://komteksky.norkart.no/MinRenovasjon.Api/api/tommekalender/?gatenavn=[gatenavn]&gatekode=[gatekode]&husnr=[husnr]&fraDato=[fra_dato]&dato=[til_dato]&api-version=2"
NUM_MONTHS = 6
STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""