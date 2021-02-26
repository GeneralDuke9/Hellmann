from itertools import islice
from typing import Any, Iterator

import requests

from common import Update

stations_mapping = {
    "215": "Voorschoten",
    "235": "De Kooy",
    "240": "Schiphol",
    "242": "Vlieland",
    "249": "Berkhout",
    "251": "Hoorn (Terschelling)",
    "257": "Wijk aan Zee",
    "260": "De Bilt",
    "267": "Stavoren",
    "269": "Lelystad",
    "270": "Leeuwarden",
    "273": "Marknesse",
    "275": "Deelen",
    "277": "Lauwersoog",
    "278": "Heino",
    "279": "Hoogeveen",
    "280": "Eelde",
    "283": "Hupsel",
    "286": "Nieuw-Beerta",
    "290": "Twente",
    "310": "Vlissingen",
    "319": "Westdorpe",
    "323": "Wilhelminadorp",
    "330": "Hoek van Holland",
    "340": "Woensdrecht",
    "344": "Rotterdam",
    "348": "Cabauw",
    "350": "Gilze-Rijen",
    "356": "Herwijnen",
    "370": "Eindhoven",
    "375": "Volkel",
    "377": "Ell",
    "380": "Maastricht",
    "391": "Arcen",
}


def get_data(year: str, month: str, day: str) -> Iterator[Any]:
    knmi_url: str = "http://projects.knmi.nl/klimatologie/daggegevens/getdata_dag.cgi"

    payload = {
        "lang": "nl",
        "byear": year,
        "bmonth": month,
        "bday": day,
        "eyear": year,
        "emonth": month,
        "eday": day,
        "variabele": "TG",
        "stations": [
            "215",
            "235",
            "240",
            "242",
            "249",
            "251",
            "257",
            "260",
            "267",
            "269",
            "270",
            "273",
            "275",
            "277",
            "278",
            "279",
            "280",
            "283",
            "286",
            "290",
            "310",
            "319",
            "323",
            "330",
            "340",
            "344",
            "348",
            "350",
            "356",
            "370",
            "375",
            "377",
            "380",
            "391",
        ],
        "submit": "Download+data+set",
    }
    response = requests.get(knmi_url, params=payload)
    update = response.iter_lines()
    return update


def knmi_update() -> list[Update]:
    update: list[Update] = []
    print("Provide date (yyyymmdd)")
    date = input()
    year = str(date[:4])
    month = str(date[4:6])
    day = str(date[6:])
    raw_update = get_data(year, month, day)
    for line in islice(raw_update, 45, None):
        station_no, _, value = line.decode().split(",")
        station = int(station_no)
        increment = int(value)
        if increment < 0:
            update.append(Update(stations_mapping[str(station)], int(-increment)))

    return update
