import requests
import json
import datetime

CONST_KOMMUNE_NUMMER = "Kommunenr"
CONST_APP_KEY = "RenovasjonAppKey"
CONST_URL_FRAKSJONER = 'https://komteksky.norkart.no/komtek.renovasjonwebapi/api/fraksjoner'
CONST_URL_TOMMEKALENDER = 'https://komteksky.norkart.no/komtek.renovasjonwebapi/api/tommekalender?' \
                          'gatenavn=[gatenavn]&gatekode=[gatekode]&husnr=[husnr]'

KOMMUNE_NUMMER = "0712"
APP_KEY = "AE13DEEC-804F-4615-A74E-B4FAC11F0A30"

CONST_DATA_FILENAME = "min_renovasjon.dat"
CONST_DATA_HEADER_COMMENT = '# Auto-generated file. Do not edit.'


def _get_tommekalender(gatenavn, gatekode, husnr):
    header = {CONST_KOMMUNE_NUMMER: KOMMUNE_NUMMER, CONST_APP_KEY: APP_KEY}

    url = CONST_URL_TOMMEKALENDER
    url = url.replace('[gatenavn]', gatenavn)
    url = url.replace('[gatekode]', gatekode)
    url = url.replace('[husnr]', husnr)

    response = requests.get(url, headers=header)
    if response.status_code == requests.codes.ok:
        data = response.text
        return data
    else:
        print(response.status_code)
        return None


def _get_fraksjoner():
    header = {CONST_KOMMUNE_NUMMER: KOMMUNE_NUMMER, CONST_APP_KEY: APP_KEY}
    url = CONST_URL_FRAKSJONER

    response = requests.get(url, headers=header)
    if response.status_code == requests.codes.ok:
        data = response.text
        return data
    else:
        print(response.status_code)
        return None


def _read_from_file():
    try:
        file = open(CONST_DATA_FILENAME)

        lines = file.readlines()
        tommekalender = lines[1]
        fraksjoner = lines[2]

        file.close()

        print("RETURNING CONTENT FROM FILE")
        return tuple((tommekalender, fraksjoner))

    except FileNotFoundError:
        print("FILE NOT FOUND")
        return None


def _write_to_file(tommekalender, fraksjoner):
    print("WRITING CONTENT TO FILE")

    file = open(CONST_DATA_FILENAME, "w")

    file.write("{}\n".format(CONST_DATA_HEADER_COMMENT))
    file.write("{}\n".format(tommekalender))
    file.write("{}\n".format(fraksjoner))

    file.close()


def _get_data(read_from_file=True):
    data = None

    if read_from_file:
        data = _read_from_file()

    if data is None:
        print("NO CURRENT DATA FROM FILE. FETCHING FROM WEB. ")

        tommekalender = _get_tommekalender('Kalli%C3%A5sen', '11700', '1')
        fraksjoner = _get_fraksjoner()
        data = tuple((tommekalender, fraksjoner))

        if fraksjoner is not None and tommekalender is not None:
            _write_to_file(tommekalender, fraksjoner)

    return data


def get_calender():
    data = _get_data()
    if data is None:
        print("NO DATA")
        return None

    # Sjekker om data er utløpt.
    # Hvis ja setter vi data = None og henter nye data

    # Sjekker linje 2 og henter ut første dato. Dersom denne er tilbake i tid henter vi nye data.
    # data = None

    tommekalender, fraksjoner = data
    tommekalender_json = json.loads(tommekalender)
    fraksjoner_json = json.loads(fraksjoner)
    kalender_list = []

    for calender_entry in tommekalender_json:
        fraksjon_id = calender_entry['FraksjonId']

        tommedato_forste, tommedato_neste = calender_entry['Tommedatoer']

        # Sjekker tommedato

        tommedato_forste = datetime.datetime.strptime(tommedato_forste, "%Y-%m-%dT%H:%M:%S").strftime("%d-%m-%Y")
        tommedato_neste = datetime.datetime.strptime(tommedato_neste, "%Y-%m-%dT%H:%M:%S").strftime("%d-%m-%Y")

        for fraksjon in fraksjoner_json:
            if fraksjon['Id'] == fraksjon_id:
                fraksjon_navn = fraksjon['Navn']
                fraksjon_ikon = fraksjon['Ikon']

                kalender_list.append((fraksjon_id, fraksjon_navn, fraksjon_ikon, tommedato_forste, tommedato_neste))
                continue

    return kalender_list


def main():
    kalender = get_calender()
    print(kalender)


main()
