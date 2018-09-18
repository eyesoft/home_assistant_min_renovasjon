import requests
import json
from datetime import date
from datetime import datetime

CONST_KOMMUNE_NUMMER = "Kommunenr"
CONST_APP_KEY = "RenovasjonAppKey"
CONST_URL_FRAKSJONER = 'https://komteksky.norkart.no/komtek.renovasjonwebapi/api/fraksjoner'
CONST_URL_TOMMEKALENDER = 'https://komteksky.norkart.no/komtek.renovasjonwebapi/api/tommekalender?' \
                          'gatenavn=[gatenavn]&gatekode=[gatekode]&husnr=[husnr]'

KOMMUNE_NUMMER = "0712"
APP_KEY = "AE13DEEC-804F-4615-A74E-B4FAC11F0A30"

CONST_DATA_FILENAME = "min_renovasjon.dat"
CONST_DATA_HEADER_COMMENT = '# Auto-generated file. Do not edit.'


# noinspection PyShadowingNames
class MinRenovasjon:
    def __init__(self, gatenavn, gatekode, husnr):
        self.gatenavn = gatenavn
        self.gatekode = gatekode
        self.husnr = husnr
        pass

    def _get_tommekalender_from_web_api(self):
        header = {CONST_KOMMUNE_NUMMER: KOMMUNE_NUMMER, CONST_APP_KEY: APP_KEY}

        url = CONST_URL_TOMMEKALENDER
        url = url.replace('[gatenavn]', self.gatenavn)
        url = url.replace('[gatekode]', self.gatekode)
        url = url.replace('[husnr]', self.husnr)

        response = requests.get(url, headers=header)
        if response.status_code == requests.codes.ok:
            data = response.text
            return data
        else:
            print(response.status_code)
            return None

    @staticmethod
    def _get_fraksjoner_from_web_api():
        header = {CONST_KOMMUNE_NUMMER: KOMMUNE_NUMMER, CONST_APP_KEY: APP_KEY}
        url = CONST_URL_FRAKSJONER

        response = requests.get(url, headers=header)
        if response.status_code == requests.codes.ok:
            data = response.text
            return data
        else:
            print(response.status_code)
            return None

    @staticmethod
    def _read_from_file():
        try:
            print("READING CONTENT FROM FILE")

            file = open(CONST_DATA_FILENAME)

            lines = file.readlines()
            tommekalender = lines[1]
            fraksjoner = lines[2]

            file.close()

            return tuple((tommekalender, fraksjoner))

        except FileNotFoundError:
            print("FILE NOT FOUND")
            return None

    @staticmethod
    def _write_to_file(tommekalender, fraksjoner):
        print("WRITING CONTENT TO FILE")

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

    def get_calendar_list(self, refresh=False):
        data = None

        if not refresh:
            data = self._read_from_file()

        if refresh or data is None:
            print("REFRESH OR NO DATA. FETCHING FROM WEB.")
            tommekalender, fraksjoner = self._get_from_web_api()
        else:
            tommekalender, fraksjoner = data

        kalender_list = self._parse_calendar_list(tommekalender, fraksjoner)

        check_for_refresh = False
        if not refresh:
            check_for_refresh = self._check_for_refresh_of_data(kalender_list)

        if check_for_refresh:
            print("REFRESHING DATA...")
            kalender_list = self.get_calendar_list(refresh=True)

        print("RETURNING CALENDAR LIST")
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
        print("CHECKING IF DATA NEEDS REFRESH")

        for entry in kalender_list:
            _, _, _, tommedato_forste, tommedato_neste = entry

            if tommedato_forste.date() < date.today() or tommedato_neste.date() < date.today():
                print("DATA NEEDS REFRESH")
                return True

        return False


min_renovasjon = MinRenovasjon('Kalli%C3%A5sen', '11700', '1')
kalender_list = min_renovasjon.get_calendar_list()

for fraksjon_id, fraksjon_navn, fraksjon_ikon, tommedato_forste, tommedato_neste in kalender_list:
    print(fraksjon_id)
    print(fraksjon_navn)
    print(fraksjon_ikon)
    print(tommedato_forste.strftime("%d-%m-%Y"))
    print(tommedato_neste.strftime("%d-%m-%Y"))
