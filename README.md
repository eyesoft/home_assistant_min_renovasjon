# Min Renovasjon

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant integration of the norwegian Min Renovasjon app.

## Installation
Under HACS -> Integrations, add custom repository "https://github.com/eyesoft/home_assistant_min_renovasjon/" with Category "Integration". Select the newly added integration named "Min renovasjon" and install it.

## Configuration

To enable the use of Min Renovasjon in your installation, add the following to your configuration.yaml file:

```
min_renovasjon:
  street_name: "Min gate"
  house_no: "12"
  street_code: "12345"
  county_id: "1234"
  date_format: "None"
```

+ **street_name** _(string) (Requred)_: The name of the street without house number, e.g. "Slottsplassen".
+ **house_no** _(string) (Requred)_: The number of the house, e.g. "1". 
+ **street_code** _(string) (Requred)_: Can be found with REST-API call.
+ **county_id** _(string) (Requred)_: Can be found with REST-API call.
+ **date_format** _(string) (Requred)_: Defaults to "%d/%m/%Y" if not specified. If set to "None" no formatting of the date is performed. 

#### REST-API call to fetch street_code and county_id:

```
https://ws.geonorge.no/adresser/v1/#/default/get_sok
https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012
```
"street_code" equals to "adressekode" and "county_id" equals to "kommunenummer". 

#### Fraction sensors

One sensor will be added for each fraction specified in your configuration.yaml file.

```
sensor:
  - platform: min_renovasjon
    fraction_id:
      - 1
      - 2
      - 3
      - 19
```

**fraction_id** _(int)(Required)_: One or more fractions for which a sensor is to be set up. ID's might be different depending on county. Turn on debug logging in Home Asstistant to log the list of fractions 
(https://www.home-assistant.io/components/logger/).
```
1: Restavfall
2: Papir
3: Matavfall
4: Glass/Metallemballasje
5: Drikkekartonger
6: Spesialavfall
8: Trevirke
9: Tekstiler
10: Hageavfall
11: Metaller
12: Hvitevarer/EE-avfall
13: Papp
14: Møbler
19: Plastemballasje
23: Nedgravd løsning
24: GlassIGLO
25: Farlig avfall
26: Matavfall hytter
27: Restavfall hytter  
28: Papir hytter
```

