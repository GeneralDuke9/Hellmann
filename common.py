from dataclasses import dataclass


@dataclass
class Update:
    station: str
    value: int
