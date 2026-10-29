from enum import StrEnum

from monopoly.domain.board import STANDARD_BOARD, Board, PropertySquare
from monopoly.domain.errors import (
    GameAlreadyStartedError,
    GameFullError,
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

MAX_PLAYER_NAME_LENGTH = 20


class GameStatus(StrEnum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class Game:
    """The game aggregate: every rule change goes through `join` and `play_turn`."""

    def __init__(self, code: str, seats: int, board: Board, rules: GameRules) -> None:
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
        if not rules.min_seats <= seats <= rules.max_seats:
            raise InvalidSeatCountError(
                f"Seats must be between {rules.min_seats} and {rules.max_seats}, got {seats}."
            )
        return cls(code=code, seats=seats, board=board, rules=rules)

    # --- read-only accessors ----------------------------------------------------------

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

    # --- commands ---------------------------------------------------------------------

    def join(self, player_name: str) -> tuple[Player, list[GameEvent]]:
        if self._status is not GameStatus.WAITING:
            raise GameAlreadyStartedError("The game has already started.")
        # Unreachable while the game starts on the last seat, kept to protect the invariant.
        if len(self._players) >= self._seats:
            raise GameFullError("The game is full.")
        name = player_name.strip()
        if not 1 <= len(name) <= MAX_PLAYER_NAME_LENGTH:
            raise InvalidPlayerNameError(
                f"Player name must be 1 to {MAX_PLAYER_NAME_LENGTH} characters."
            )

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
        player = self._ensure_can_play(player_id)
        if not 1 <= roll <= self._rules.die_faces:
            raise InvalidRollError(f"A roll must be between 1 and {self._rules.die_faces}.")

        events: list[GameEvent] = [DiceRolled(player_id=player.id, value=roll)]
        events += self._move(player, roll)
        events += self._resolve_square(player)
        events += self._end_turn()
        return events

    # --- turn steps -------------------------------------------------------------------

    def _ensure_can_play(self, player_id: str) -> Player:
        if self._status is not GameStatus.IN_PROGRESS:
            raise GameNotInProgressError("The game is not in progress.")
        player = self.player(player_id)
        if player is not self.current_player:
            raise NotYourTurnError(f"It is not {player.name}'s turn.")
        return player

    def _move(self, player: Player, roll: int) -> list[GameEvent]:
        from_position = player.position
        steps = from_position + roll
        player.position = steps % self._board.size
        events: list[GameEvent] = [
            PlayerMoved(
                player_id=player.id, from_position=from_position, to_position=player.position
            )
        ]
        # Reaching the board size means the move crossed Start or stopped on it.
        if steps >= self._board.size:
            player.money += self._rules.salary
            events.append(SalaryReceived(player_id=player.id, amount=self._rules.salary))
        return events

    def _resolve_square(self, player: Player) -> list[GameEvent]:
        index = player.position
        square = self._board.square_at(index)
        if not isinstance(square, PropertySquare):
            return []
        owner_id = self._owners.get(index)
        if owner_id is None:
            return self._buy(player, index, square)
        if owner_id == player.id:
            return []
        return self._pay_rent(player, self.player(owner_id), index, square)

    def _buy(self, player: Player, index: int, square: PropertySquare) -> list[GameEvent]:
        if player.money < square.price:
            return [PropertyUnaffordable(player_id=player.id, square_index=index)]
        player.money -= square.price
        self._owners[index] = player.id
        return [PropertyBought(player_id=player.id, square_index=index, price=square.price)]

    def _pay_rent(
        self, player: Player, owner: Player, index: int, square: PropertySquare
    ) -> list[GameEvent]:
        amount = min(square.rent, player.money)
        player.money -= amount
        owner.money += amount
        events: list[GameEvent] = [
            RentPaid(player_id=player.id, owner_id=owner.id, square_index=index, amount=amount)
        ]
        if amount < square.rent:
            events += self._bankrupt(player, creditor=owner)
        return events

    def _bankrupt(self, player: Player, creditor: Player) -> list[GameEvent]:
        player.is_bankrupt = True
        self._owners = {
            index: owner_id for index, owner_id in self._owners.items() if owner_id != player.id
        }
        return [PlayerBankrupted(player_id=player.id, creditor_id=creditor.id)]

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
