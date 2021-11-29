from __future__ import annotations

from dataclasses import dataclass, field
import datetime

import requests

STATIONS_MAPPING = {
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


@dataclass
class Station:
    name: str
    score: int
    rank: int = 0
    new_rank: int = 0
    gain: int = 0

    def __lt__(self, other: Station):
        if self.score == other.score:
            return self.name > other.name
        else:
            return self.score < other.score


@dataclass
class Update:
    station_name: str
    value: int


@dataclass
class Ranking:
    stations: list[Station] = field(default_factory=list)

    def update_values_ranks_and_write_files(self, new_values: list[Update]):
        station_by_name = {station.name: station for station in self.stations}
        for update in new_values:
            try:
                station = station_by_name[update.station_name]
                station.gain = update.value
                station.score += station.gain
            except KeyError:
                self.stations.append(Station(name=update.station_name, score=update.value))
        self._update_ranks()
        self._write_ranking_to_file()
        self._write_board_update()

    def _write_board_update(self):
        with open("board_update.txt", "w") as datafile:
            for station in self.stations:
                board_line = build_board_line(station)
                datafile.write(f"{board_line}\n")

    def _update_ranks(self):
        self.stations.sort(reverse=True)
        for station in self.stations:
            station.new_rank = self.stations.index(station) + 1
            if station.new_rank > 1:
                higher_station = self.stations[self.stations.index(station) - 1]
                if station.score == higher_station.score:
                    station.new_rank = higher_station.new_rank

    def _write_ranking_to_file(self):
        with open("ranking.txt", "w") as datafile:
            for station in self.stations:
                datafile.write(f"{station.new_rank},{station.name},{station.score}\n")


def to_comma_string(value: float | int) -> str:
    return str(float(value) / 10.0).replace(".", ",")


def build_board_line(station: Station) -> str:
    gain = ""
    rank_change = station.rank - station.new_rank
    rank = ""
    score = to_comma_string(station.score)
    if station.rank == 0:
        return f"[color=orange]{station.new_rank}. {station.name} {score}[/color]"
    if station.gain != 0:
        gain = f" [color=grey][i]+{to_comma_string(station.gain)}[/i][/color]"
    if rank_change > 0:
        if station.rank != 8:
            rank = f" [color=green]({station.rank})[/color]"
        else:
            rank = f" [color=green]({station.rank} )[/color]"
    elif rank_change < 0:
        if station.rank != 8:
            rank = f" [color=red]({station.rank})[/color]"
        else:
            rank = f" [color=red]({station.rank} )[/color]"
    return f"{station.new_rank}. {station.name} {score}{gain}{rank}"


def get_data(date: datetime.date) -> list[dict[str, int]]:
    knmi_url: str = "https://daggegevens.knmi.nl/klimatologie/daggegevens"
    datestring = f"{date.year}{date.month}{date.day}"
    payload = {
        "start": datestring,
        "end": datestring,
        "fmt": "json",
    }
    for var in ["TG"]:
        payload.update({f"vars[{var}]": "1"})
    for stn in STATIONS_MAPPING.keys():
        payload.update({f"stns[{stn}]": "1"})
    response = requests.post(knmi_url, params=payload)
    return response.json()


def get_knmi_update(date: datetime.date = None) -> list[Update]:
    if date is None:
        date = datetime.date.today() - datetime.timedelta(days=1)
    raw_update = get_data(date)
    update = [
        Update(STATIONS_MAPPING[station_data["station_code"]], -station_data["TG"])
        for station_data in raw_update
        if station_data["TG"] < 0
    ]
    return update


def read_ranking() -> Ranking:
    stations: list[Station] = []
    try:
        with open("ranking.txt", "r") as datafile:
            for line in datafile:
                rank, name, score = line.split(",")
                stations.append(Station(name=name, rank=int(rank), score=int(score)))
    except FileNotFoundError:
        return Ranking()

    return Ranking(stations=stations)


def print_update_summary(update: list[Update]):
    no_stations = len(update)
    average = sum([u.value for u in update]) / no_stations / 10.0
    print(f"{no_stations} stations scored an average of {average} points")


def main():
    ranking = read_ranking()
    update = get_knmi_update()
    if len(update) == 0:
        print("No update received")
        return
    print_update_summary(update)
    ranking.update_values_ranks_and_write_files(update)


if __name__ == "__main__":
    main()
