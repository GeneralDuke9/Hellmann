import datetime
from typing import Any, Iterator

import requests

from common import Update

stations_mapping = {
    215: "Voorschoten",
    235: "De Kooy",
    240: "Schiphol",
    242: "Vlieland",
    249: "Berkhout",
    251: "Hoorn (Terschelling)",
    257: "Wijk aan Zee",
    260: "De Bilt",
    267: "Stavoren",
    269: "Lelystad",
    270: "Leeuwarden",
    273: "Marknesse",
    275: "Deelen",
    277: "Lauwersoog",
    278: "Heino",
    279: "Hoogeveen",
    280: "Eelde",
    283: "Hupsel",
    286: "Nieuw-Beerta",
    290: "Twente",
    310: "Vlissingen",
    319: "Westdorpe",
    323: "Wilhelminadorp",
    330: "Hoek van Holland",
    340: "Woensdrecht",
    344: "Rotterdam",
    348: "Cabauw",
    350: "Gilze-Rijen",
    356: "Herwijnen",
    370: "Eindhoven",
    375: "Volkel",
    377: "Ell",
    380: "Maastricht",
    391: "Arcen",
}


def get_data(datestring: str) -> Iterator[Any]:
    knmi_url: str = "https://daggegevens.knmi.nl/klimatologie/daggegevens"

    payload = {
        "start": datestring,
        "end": datestring,
        "fmt": "json",
    }
    for var in ["TG"]:
        payload.update({f"vars[{var}]": "1"})
    for stn in stations_mapping.keys():
        payload.update({f"stns[{stn}]": "1"})
    response = requests.post(knmi_url, params=payload)
    return response.json()


def validate_input(datestring: str):
    year = int(datestring[:4])
    month = int(datestring[4:6])
    day = int(datestring[6:])
    datetime.date(year, month, day)


def knmi_update() -> list[Update]:
    print("Provide date (yyyymmdd)")
    date = input()
    validate_input(date)
    raw_update = get_data(date)
    update = [
        Update(stations_mapping[station_data["station_code"]], -station_data["TG"])
        for station_data in raw_update
        if station_data["TG"] < 0
    ]
    return update
