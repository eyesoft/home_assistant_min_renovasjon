# home-assistant-custom-components
Custom components for Home Assistant (https://www.home-assistant.io/)

Min Renovasjon:

```
min_renovasjon:
  street_name: "Min gate"
  street_code: "00000"
  house_no: "0"
  county_id: "0000"


sensor:
  - platform: min_renovasjon
    fraction_id:
      - 1
      - 2
      - 3
      - 19
  ```
  
1: Restavfall

2: Papir

3: Matavfall

11: Metall

19: Plast
  