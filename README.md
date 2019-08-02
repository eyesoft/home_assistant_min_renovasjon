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

Fraksjoner:  
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