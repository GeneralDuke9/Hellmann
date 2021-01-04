from itertools import islice
from sys import exit, stdin
from typing import List

from get_knmi import get_data, stations_mapping


class Update:
    station: str
    value: int

    def __init__(self, _station: str, _value: int):
        self.station = _station
        self.value = _value


class Station:
    name: str
    rank: int
    new_rank: int
    score: int
    gain: int

    def __init__(self, _name: str, _rank: int, _score: int):
        self.name = _name
        self.rank = _rank
        self.score = _score
        self.gain = 0

    def __lt__(self, other):
        if self.score == other.score:
            return self.name > other.name
        else:
            return self.score < other.score


class Ranking:
    stations: List[Station] = []

    def update_values(self, new_values: List[Update]):
        names = [station.name for station in self.stations]
        for update in new_values:
            if update.station in names:
                idx = names.index(update.station)
                station = self.stations[idx]
                station.gain = update.value
                station.score += station.gain
            else:
                self.stations.append(Station(update.station, 0, update.value))

    def update_ranks(self):
        self.stations.sort(reverse=True)
        for station in self.stations:
            station.new_rank = self.stations.index(station) + 1
            if station.new_rank > 1:
                higher_station = self.stations[self.stations.index(station) - 1]
                if station.score == higher_station.score:
                    station.new_rank = higher_station.new_rank


def read_stations() -> Ranking:
    ranks = Ranking()
    try:
        with open("ranking.txt", "r") as datafile:
            for line in datafile:
                (rank, name, score) = line.split(",")
                ranks.stations.append(Station(name, int(rank), int(score)))
    except FileNotFoundError:
        pass

    return ranks


def get_new_values() -> List[Update]:
    method = get_input_method()
    if method == 1:
        new_values = prompt_update()
    elif method == 2:
        new_values = knmi_update()
    else:
        print("Unknown entry, exit")
        exit(1)
    if new_values == []:
        print("No update received, exit")
        exit(1)
    return new_values


def get_input_method() -> int:
    print("Input 1 for manual input, input 2 for KNMI input:")
    input_method = input()
    try:
        method = int(input_method)
    except TypeError:
        print("Unknown entry, exit")
        exit(1)
    return method


def prompt_update() -> List[Update]:
    update: List[Update] = []
    print("Enter update as name,value")
    print("End with Ctrl+D")
    for line in stdin:
        (name, value) = line.split(",")
        # Todo: verify input
        update.append(Update(name, int(10 * float(value))))

    return update


def knmi_update() -> List[Update]:
    update: List[Update] = []
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


def write_file(ranking: Ranking):
    with open("ranking.txt", "w") as datafile:
        for station in ranking.stations:
            datafile.write(f"{station.new_rank},{station.name},{station.score}\n")


def get_board_update(ranking: Ranking):
    with open("board_update.txt", "w") as datafile:
        for station in ranking.stations:
            orange = ""
            orange_end = ""
            gain = ""
            rank_change = station.rank - station.new_rank
            rank = ""
            score = str(float(station.score) / 10.0).replace(".", ",")
            if station.rank == 0:
                orange = "[color=orange]"
                orange_end = "[/color]"
            else:
                if station.gain != 0:
                    gaincomma = str(float(station.gain) / 10.0).replace(".", ",")
                    gain = f" [color=grey][i]+{gaincomma}[/i][/color]"
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
            datafile.write(f"{orange}{station.new_rank}. {station.name} {score}{gain}{rank}{orange_end}\n")


def main():
    ranking: Ranking
    new_values: List[Update]

    ranking = read_stations()
    new_values = get_new_values()
    ranking.update_values(new_values)
    ranking.update_ranks()
    write_file(ranking)
    get_board_update(ranking)


if __name__ == "__main__":
    main()
