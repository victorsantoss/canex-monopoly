from dataclasses import dataclass


@dataclass
class Player:
    id: str
    name: str
    money: int
    position: int = 0
    is_bankrupt: bool = False
