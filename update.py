from __future__ import annotations

import datetime
import os
import smtplib
import ssl
from collections import defaultdict
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

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

    def update_values_and_ranks(self, new_values: list[Update], reset_ranks=True):
        station_by_name = {station.name: station for station in self.stations}
        for update in new_values:
            try:
                station = station_by_name[update.station_name]
                station.gain = update.value
                station.score += station.gain
            except KeyError:
                self.stations.append(Station(name=update.station_name, score=update.value))
        self._update_ranks()
        if reset_ranks:
            self._reset_ranks()

    def update_values_ranks_and_write_files(self, new_values: list[Update]):
        self.update_values_and_ranks(new_values, reset_ranks=False)
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

    def _reset_ranks(self):
        for station in self.stations:
            station.gain = 0
            station.rank = station.new_rank


class MailSender:
    def __init__(self, update: list[Update], ranking: Ranking):
        self.ranking = ranking
        self.update = update
        SMTP_PORT = 465
        sender_email = os.getenv("SENDER_USERNAME")
        password = os.getenv("SENDER_PASSWORD")
        if sender_email is None or password is None:
            if sender_email is None:
                print("Sender mail not set")
            if password is None:
                print("Password not set")
            raise ValueError
        self.sender_email = sender_email
        context = ssl.create_default_context()
        gmail_smtp = "smtp.gmail.com"

        with smtplib.SMTP_SSL(gmail_smtp, SMTP_PORT, context=context) as server:
            server.login(self.sender_email, password)
            self._send_mails(server)

    def _send_mails(self, server: smtplib.SMTP):
        recipients_string = os.getenv("RECIPIENTS")
        board_recipients_string = os.getenv("BOARD_RECIPIENTS")
        if recipients_string is not None:
            recipients = recipients_string.split(",")
            message = self._build_message()
            server.sendmail(self.sender_email, recipients, message.as_string())
        if board_recipients_string is not None:
            board_recipients = board_recipients_string.split(",")
            message = self._build_message(is_board_update=True)
            server.sendmail(self.sender_email, board_recipients, message.as_string())

    def _create_board_update_body(self) -> str:
        return "\n".join(build_board_line(station) for station in self.ranking.stations)

    def _create_body(self) -> str:
        return "\n".join(f"{item.station_name}: {item.value/10}" for item in self.update)

    def _build_message(self, is_board_update: bool = False) -> MIMEMultipart:
        if is_board_update:
            subject = f"Hellmann board update {datetime.date.today() - datetime.timedelta(days=1)}"
            body = self._create_board_update_body()
        else:
            subject = f"Hellmann update {datetime.date.today() - datetime.timedelta(days=1)}"
            body = self._create_body()
        message_text = MIMEMultipart("alternative")

        message_text.attach(MIMEText(body, "plain"))
        message = MIMEMultipart("mixed")

        message.attach(message_text)
        message["From"] = self.sender_email
        message["Subject"] = subject
        return message


def to_comma_string(value: float | int) -> str:
    return str(float(value) / 10.0).replace(".", ",")


def missing_value_string(station_data: dict[str, Any]):
    station_name = STATIONS_MAPPING[station_data["station_code"]]
    date = datetime.datetime.strptime(station_data["date"], "%Y-%m-%dT%H:%M:%S.000Z").date()
    return f"WARNING: No value for {station_name} on {date}"


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


def get_data(start_date: datetime.date, end_date: datetime.date) -> list[dict[str, Any]]:
    knmi_url: str = "https://daggegevens.knmi.nl/klimatologie/daggegevens"
    start_datestring = datetime.date.strftime(start_date, "%Y%m%d")
    end_datestring = datetime.date.strftime(end_date, "%Y%m%d")
    payload = {
        "start": start_datestring,
        "end": end_datestring,
        "fmt": "json",
        "vars[TG]": "1",
    }
    for stn in STATIONS_MAPPING.keys():
        payload.update({f"stns[{stn}]": "1"})
    response = requests.post(knmi_url, params=payload)
    return response.json()


def get_knmi_update(start_date: datetime.date, date_to_fetch: datetime.date) -> dict[datetime.date, list[Update]]:
    raw_update = get_data(start_date, date_to_fetch)
    updates_by_date: dict[datetime.date, list[Update]] = defaultdict(list)
    for station_data in raw_update:
        if station_data["TG"] is None:
            print(missing_value_string(station_data))
            continue
        if (scored_points := -station_data["TG"]) <= 0:
            continue
        date = datetime.datetime.strptime(station_data["date"], "%Y-%m-%dT%H:%M:%S.000Z").date()
        update = Update(STATIONS_MAPPING[station_data["station_code"]], scored_points)
        updates_by_date[date].append(update)
    return updates_by_date


def print_update_summary(update: list[Update]):
    no_stations = len(update)
    average = sum([u.value for u in update]) / no_stations / 10.0
    print(f"{no_stations} stations scored an average of {average} points")


def main():
    start_date = datetime.date(2021, 11, 1)
    date_to_fetch = datetime.date.today() - datetime.timedelta(days=1)
    update = get_knmi_update(start_date, date_to_fetch)
    today_update = update[date_to_fetch]
    if len(today_update) == 0:
        print("No update received")
        return
    print_update_summary(today_update)
    ranking = Ranking()
    this_date = start_date
    while this_date != date_to_fetch:
        this_update = update[this_date]
        if len(this_update) > 0:
            ranking.update_values_and_ranks(update[this_date])
        this_date = this_date + datetime.timedelta(days=1)
    ranking.update_values_ranks_and_write_files(today_update)
    MailSender(today_update, ranking)


if __name__ == "__main__":
    main()
