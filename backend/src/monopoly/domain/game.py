from dataclasses import replace
from enum import StrEnum

from monopoly.domain.board import STANDARD_BOARD, Board, PropertySquare
from monopoly.domain.errors import (
    GameAlreadyStartedError,
    GameNotInProgressError,
    InvalidPlayerNameError,
    InvalidRollError,
    InvalidSeatCountError,
    NotYourTurnError,
    UnknownPlayerError,
)
from monopoly.domain.events import (
    DiceRolled,
    GameEvent,
    GameStarted,
    GameWon,
    PlayerBankrupted,
    PlayerJoined,
    PlayerMoved,
    PropertyBought,
    PropertyUnaffordable,
    RentPaid,
    SalaryReceived,
    TurnPassed,
)
from monopoly.domain.player import Player
from monopoly.domain.rules import GameRules


class GameStatus(StrEnum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class Game:
    def __init__(self, code: str, seats: int, board: Board, rules: GameRules) -> None:
        if not rules.min_seats <= seats <= rules.max_seats:
            raise InvalidSeatCountError(
                f"Seats must be between {rules.min_seats} and {rules.max_seats}, got {seats}."
            )
        self._code = code
        self._seats = seats
        self._board = board
        self._rules = rules
        self._status = GameStatus.WAITING
        self._players: list[Player] = []
        self._owners: dict[int, str] = {}
        self._current_index: int | None = None
        self._winner_id: str | None = None

    @classmethod
    def create(
        cls,
        code: str,
        seats: int,
        board: Board = STANDARD_BOARD,
        rules: GameRules = GameRules(),  # noqa: B008 - GameRules is frozen, sharing it is safe
    ) -> "Game":
        return cls(code=code, seats=seats, board=board, rules=rules)

    @property
    def code(self) -> str:
        return self._code

    @property
    def status(self) -> GameStatus:
        return self._status

    @property
    def seats(self) -> int:
        return self._seats

    @property
    def board(self) -> Board:
        return self._board

    @property
    def rules(self) -> GameRules:
        return self._rules

    @property
    def players(self) -> tuple[Player, ...]:
        return tuple(self._players)

    @property
    def current_player(self) -> Player | None:
        if self._current_index is None:
            return None
        return self._players[self._current_index]

    @property
    def winner(self) -> Player | None:
        if self._winner_id is None:
            return None
        return self.player(self._winner_id)

    def owner_of(self, square_index: int) -> str | None:
        return self._owners.get(square_index)

    def player(self, player_id: str) -> Player:
        for candidate in self._players:
            if candidate.id == player_id:
                return candidate
        raise UnknownPlayerError(f"Unknown player {player_id!r}.")

    def join(self, player_name: str) -> tuple[Player, list[GameEvent]]:
        if self._status is not GameStatus.WAITING:
            raise GameAlreadyStartedError("The game has already started.")
        name = player_name.strip()
        max_length = self._rules.max_player_name_length
        if not 1 <= len(name) <= max_length:
            raise InvalidPlayerNameError(f"Player name must be 1 to {max_length} characters.")

        player = Player(
            id=f"p{len(self._players) + 1}", name=name, money=self._rules.starting_money
        )
        self._players.append(player)
        events: list[GameEvent] = [PlayerJoined(player_id=player.id, player_name=player.name)]
        if len(self._players) == self._seats:
            self._status = GameStatus.IN_PROGRESS
            self._current_index = 0
            events.append(GameStarted())
        return player, events

    def play_turn(self, player_id: str, roll: int) -> list[GameEvent]:
        self._ensure_can_play(player_id)
        if not 1 <= roll <= self._rules.die_faces:
            raise InvalidRollError(f"A roll must be between 1 and {self._rules.die_faces}.")

        events: list[GameEvent] = [DiceRolled(player_id=player_id, value=roll)]
        events += self._move(player_id, roll)
        events += self._resolve_square(player_id)
        events += self._end_turn()
        return events

    def _ensure_can_play(self, player_id: str) -> None:
        if self._status is not GameStatus.IN_PROGRESS:
            raise GameNotInProgressError("The game is not in progress.")
        player = self.player(player_id)
        current = self.current_player
        if current is None or current.id != player.id:
            raise NotYourTurnError(f"It is not {player.name}'s turn.")

    def _save(self, updated: Player) -> None:
        index = next(i for i, candidate in enumerate(self._players) if candidate.id == updated.id)
        self._players[index] = updated

    def _move(self, player_id: str, roll: int) -> list[GameEvent]:
        from_position = self.player(player_id).position
        distance_from_start = from_position + roll
        to_position = distance_from_start % self._board.size
        self._save(replace(self.player(player_id), position=to_position))
        events: list[GameEvent] = [
            PlayerMoved(player_id=player_id, from_position=from_position, to_position=to_position)
        ]
        reached_start = distance_from_start >= self._board.size
        if reached_start:
            player = self.player(player_id)
            self._save(replace(player, money=player.money + self._rules.salary))
            events.append(SalaryReceived(player_id=player_id, amount=self._rules.salary))
        return events

    def _resolve_square(self, player_id: str) -> list[GameEvent]:
        index = self.player(player_id).position
        square = self._board.square_at(index)
        if not isinstance(square, PropertySquare):
            return []
        owner_id = self._owners.get(index)
        if owner_id is None:
            return self._buy(player_id, index, square)
        if owner_id == player_id:
            return []
        return self._pay_rent(player_id, owner_id, index, square)

    def _buy(self, player_id: str, index: int, square: PropertySquare) -> list[GameEvent]:
        player = self.player(player_id)
        if player.money < square.price:
            return [PropertyUnaffordable(player_id=player_id, square_index=index)]
        self._save(replace(player, money=player.money - square.price))
        self._owners[index] = player_id
        return [PropertyBought(player_id=player_id, square_index=index, price=square.price)]

    def _pay_rent(
        self, player_id: str, owner_id: str, index: int, square: PropertySquare
    ) -> list[GameEvent]:
        rent = self._rules.rent_for(square.price)
        player = self.player(player_id)
        amount = min(rent, player.money)
        self._save(replace(player, money=player.money - amount))
        owner = self.player(owner_id)
        self._save(replace(owner, money=owner.money + amount))
        events: list[GameEvent] = [
            RentPaid(player_id=player_id, owner_id=owner_id, square_index=index, amount=amount)
        ]
        if amount < rent:
            events += self._bankrupt(player_id, creditor_id=owner_id)
        return events

    def _bankrupt(self, player_id: str, creditor_id: str) -> list[GameEvent]:
        self._save(replace(self.player(player_id), is_bankrupt=True))
        self._owners = {
            index: owner_id for index, owner_id in self._owners.items() if owner_id != player_id
        }
        return [PlayerBankrupted(player_id=player_id, creditor_id=creditor_id)]

    def _end_turn(self) -> list[GameEvent]:
        remaining = [candidate for candidate in self._players if not candidate.is_bankrupt]
        if len(remaining) == 1:
            winner = remaining[0]
            self._status = GameStatus.FINISHED
            self._current_index = None
            self._winner_id = winner.id
            return [GameWon(player_id=winner.id)]
        return [TurnPassed(player_id=self._advance_turn().id)]

    def _advance_turn(self) -> Player:
        assert self._current_index is not None
        index = self._current_index
        while True:
            index = (index + 1) % len(self._players)
            if not self._players[index].is_bankrupt:
                self._current_index = index
                return self._players[index]
