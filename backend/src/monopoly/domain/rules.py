from dataclasses import dataclass


@dataclass(frozen=True)
class GameRules:
    starting_money: int = 1500
    salary: int = 200
    min_seats: int = 2
    max_seats: int = 4
    die_faces: int = 6
