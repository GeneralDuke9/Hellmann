from __future__ import annotations


from sys import stdin

from get_knmi import knmi_update
from common import Update


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
    stations: list[Station] = []

    def update_values(self, new_values: list[Update]):
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


def get_new_values() -> list[Update]:
    method = get_input_method()
    if method == 1:
        return prompt_update()
    elif method == 2:
        new_values = knmi_update()
        show_update(new_values)
        return new_values
    raise ValueError("Unknown entry")


def update_summary(update: list[Update]):
    no_stations = len(update)
    average = sum([u.value for u in update]) / no_stations / 10.0
    print(f"{no_stations} stations scored an average of {average} points")


def get_input_method() -> int:
    print("Input 1 for manual input, input 2 for KNMI input:")
    try:
        return int(input())
    except ValueError:
        raise ValueError("Unknown entry")


def prompt_update() -> list[Update]:
    update: list[Update] = []
    print("Enter update as name,value")
    print("End with Ctrl+D")
    for line in stdin:
        try:
            (name, value) = line.split(",")
        except ValueError:
            print("Enter name,value")
        else:
            try:
                update.append(Update(name, int(10 * float(value))))
            except ValueError:
                print("'value' should be a number")

    return update


def show_update(update: list[Update]):
    print("\nUpdate:")
    for entry in update:
        valuecomma = to_comma_string(entry.value)
        print(f"{entry.station}: {valuecomma}")


def write_file(ranking: Ranking):
    with open("ranking.txt", "w") as datafile:
        for station in ranking.stations:
            datafile.write(f"{station.new_rank},{station.name},{station.score}\n")


def to_comma_string(value: float | int) -> str:
    return str(float(value) / 10.0).replace(".", ",")


def get_board_update(ranking: Ranking):
    with open("board_update.txt", "w") as datafile:
        for station in ranking.stations:
            orange = ""
            orange_end = ""
            gain = ""
            rank_change = station.rank - station.new_rank
            rank = ""
            score = to_comma_string(station.score)
            if station.rank == 0:
                orange = "[color=orange]"
                orange_end = "[/color]"
            else:
                if station.gain != 0:
                    gaincomma = to_comma_string(station.gain)
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
            board_line = f"{orange}{station.new_rank}. {station.name} {score}{gain}{rank}{orange_end}"
            datafile.write(f"{board_line}\n")


def main() -> int:
    ranking: Ranking
    new_values: list[Update]

    ranking = read_stations()
    try:
        new_values = get_new_values()
    except Exception as e:
        print(e)
        return 1
    if len(new_values) == 0:
        print("No update received")
        return 0
    update_summary(new_values)
    ranking.update_values(new_values)
    ranking.update_ranks()
    write_file(ranking)
    get_board_update(ranking)

    return 0


if __name__ == "__main__":
    result_code = main()
    exit(result_code)
