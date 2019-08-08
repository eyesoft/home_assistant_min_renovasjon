# home-assistant-custom-components
Custom components for Home Assistant (https://www.home-assistant.io/)

Min Renovasjon:

```
min_renovasjon:
  street_name: "Min gate"
  street_code: "12345"
  house_no: "12"
  county_id: "1234"
  date_format: "None"

sensor:
  - platform: min_renovasjon
    fraction_id:
      - 1
      - 2
      - 3
      - 19
  ```

Street_code (adressekode) and county_id (kommunenummer) can be found with this REST-API call:
```
https://ws.geonorge.no/adresser/v1/#/default/get_sok
https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012
```

fraction_id (might be different depending on county):
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

date_format defaults to "%d/%m/%Y" if not specified. If set to "None" no formatting of the date is performed. 
