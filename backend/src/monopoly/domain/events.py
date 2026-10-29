"""Domain events, one per `GameEvent` type of the API contract, in the order they occur."""

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class PlayerJoined:
    player_id: str
    player_name: str


@dataclass(frozen=True)
class GameStarted:
    pass


@dataclass(frozen=True)
class DiceRolled:
    player_id: str
    value: int


@dataclass(frozen=True)
class PlayerMoved:
    player_id: str
    from_position: int
    to_position: int


@dataclass(frozen=True)
class SalaryReceived:
    player_id: str
    amount: int


@dataclass(frozen=True)
class PropertyBought:
    player_id: str
    square_index: int
    price: int


@dataclass(frozen=True)
class PropertyUnaffordable:
    player_id: str
    square_index: int


@dataclass(frozen=True)
class RentPaid:
    player_id: str
    owner_id: str
    square_index: int
    amount: int


@dataclass(frozen=True)
class PlayerBankrupted:
    player_id: str
    creditor_id: str


@dataclass(frozen=True)
class TurnPassed:
    player_id: str


@dataclass(frozen=True)
class GameWon:
    player_id: str


GameEvent: TypeAlias = (
    PlayerJoined
    | GameStarted
    | DiceRolled
    | PlayerMoved
    | SalaryReceived
    | PropertyBought
    | PropertyUnaffordable
    | RentPaid
    | PlayerBankrupted
    | TurnPassed
    | GameWon
)
