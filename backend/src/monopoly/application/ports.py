from collections.abc import Sequence
from typing import Protocol

from monopoly.domain.events import GameEvent
from monopoly.domain.game import Game


class GameRepository(Protocol):
    def get(self, code: str) -> Game | None: ...

    def save(self, game: Game) -> None: ...


class SeatRegistry(Protocol):
    """Maps the secret token handed to a player to their seat in a game."""

    def register(self, code: str, player_id: str, token: str) -> None: ...

    def find_player_id(self, code: str, token: str) -> str | None: ...


class GameNotifier(Protocol):
    async def notify(self, game: Game, events: Sequence[GameEvent]) -> None: ...


class Dice(Protocol):
    def roll(self, faces: int) -> int: ...


class CodeGenerator(Protocol):
    def new_code(self) -> str: ...


class TokenGenerator(Protocol):
    def new_token(self) -> str: ...
