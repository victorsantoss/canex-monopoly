from dataclasses import dataclass

from monopoly.application.errors import GameNotFoundError, InvalidPlayerTokenError
from monopoly.application.ports import (
    CodeGenerator,
    Dice,
    GameNotifier,
    GameRepository,
    SeatRegistry,
    TokenGenerator,
)
from monopoly.domain.events import GameEvent
from monopoly.domain.game import Game
from monopoly.domain.rules import GameRules


@dataclass(frozen=True)
class JoinedGame:
    code: str
    player_id: str
    player_token: str


@dataclass(frozen=True)
class TurnResult:
    game: Game
    events: list[GameEvent]


# Commands never `await` between loading and saving a game: on a single event loop, that keeps two
# commands on the same game from interleaving without a lock.
class GameService:
    def __init__(
        self,
        repository: GameRepository,
        seats: SeatRegistry,
        notifier: GameNotifier,
        dice: Dice,
        codes: CodeGenerator,
        tokens: TokenGenerator,
    ) -> None:
        self._repository = repository
        self._seats = seats
        self._notifier = notifier
        self._dice = dice
        self._codes = codes
        self._tokens = tokens

    async def create_game(
        self,
        player_name: str,
        seats: int,
        rules: GameRules = GameRules(),  # noqa: B008 - GameRules is frozen, sharing it is safe
    ) -> JoinedGame:
        game = Game.create(code=self._new_code(), seats=seats, rules=rules)
        return await self._seat(game, player_name)

    async def join_game(self, code: str, player_name: str) -> JoinedGame:
        return await self._seat(self.get_game(code), player_name)

    async def play_turn(self, code: str, player_token: str) -> TurnResult:
        game = self.get_game(code)
        player_id = self._seats.find_player_id(code, player_token)
        if player_id is None:
            raise InvalidPlayerTokenError("Unknown player token for this game.")
        events = game.play_turn(player_id, self._dice.roll(game.rules.die_faces))
        self._repository.save(game)
        await self._notifier.notify(game, events)
        return TurnResult(game=game, events=events)

    def get_game(self, code: str) -> Game:
        game = self._repository.get(code)
        if game is None:
            raise GameNotFoundError(f"Game {code!r} not found.")
        return game

    async def _seat(self, game: Game, player_name: str) -> JoinedGame:
        player, events = game.join(player_name)
        token = self._tokens.new_token()
        self._repository.save(game)
        self._seats.register(game.code, player.id, token)
        await self._notifier.notify(game, events)
        return JoinedGame(code=game.code, player_id=player.id, player_token=token)

    def _new_code(self) -> str:
        code = self._codes.new_code()
        while self._repository.get(code) is not None:
            code = self._codes.new_code()
        return code
