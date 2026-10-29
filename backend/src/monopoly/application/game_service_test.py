from collections.abc import Iterator, Sequence

import pytest

from monopoly.application.errors import GameNotFoundError, InvalidPlayerTokenError
from monopoly.application.game_service import GameService, GameSettings, JoinedGame
from monopoly.domain.errors import (
    GameAlreadyStartedError,
    InvalidGameSettingsError,
    InvalidPlayerNameError,
    InvalidSeatCountError,
    NotYourTurnError,
)
from monopoly.domain.events import (
    DiceRolled,
    GameEvent,
    GameStarted,
    PlayerJoined,
    PlayerMoved,
    PropertyBought,
    TurnPassed,
)
from monopoly.domain.game import Game, GameStatus
from monopoly.domain.rules import GameRules


class DictGameRepository:
    def __init__(self) -> None:
        self.games: dict[str, Game] = {}

    def get(self, code: str) -> Game | None:
        return self.games.get(code)

    def save(self, game: Game) -> None:
        self.games[game.code] = game


class DictSeatRegistry:
    def __init__(self) -> None:
        self.seats: dict[tuple[str, str], str] = {}

    def register(self, code: str, player_id: str, token: str) -> None:
        self.seats[(code, token)] = player_id

    def find_player_id(self, code: str, token: str) -> str | None:
        return self.seats.get((code, token))


class RecordingNotifier:
    def __init__(self) -> None:
        self.notifications: list[tuple[str, list[GameEvent]]] = []

    async def notify(self, game: Game, events: Sequence[GameEvent]) -> None:
        self.notifications.append((game.code, list(events)))


class FixedDice:
    def __init__(self, value: int) -> None:
        self.value = value
        self.faces_asked: list[int] = []

    def roll(self, faces: int) -> int:
        self.faces_asked.append(faces)
        return self.value


class SequenceGenerator:
    def __init__(self, *values: str) -> None:
        self._values: Iterator[str] = iter(values)

    def new_code(self) -> str:
        return next(self._values)

    def new_token(self) -> str:
        return next(self._values)


class Fixture:
    def __init__(self, codes: Sequence[str] = ("GAME01", "GAME02", "GAME03")) -> None:
        self.repository = DictGameRepository()
        self.registry = DictSeatRegistry()
        self.notifier = RecordingNotifier()
        self.dice = FixedDice(3)
        self.service = GameService(
            repository=self.repository,
            seats=self.registry,
            notifier=self.notifier,
            dice=self.dice,
            codes=SequenceGenerator(*codes),
            tokens=SequenceGenerator("token-1", "token-2", "token-3", "token-4"),
        )


@pytest.fixture
def fixture() -> Fixture:
    return Fixture()


async def test_create_game_saves_a_waiting_game_with_the_creator_seated(
    fixture: Fixture,
) -> None:
    joined = await fixture.service.create_game("Ana", seats=2)

    assert joined == JoinedGame(code="GAME01", player_id="p1", player_token="token-1")
    game = fixture.repository.games["GAME01"]
    assert game.status is GameStatus.WAITING
    assert [player.name for player in game.players] == ["Ana"]
    assert fixture.registry.find_player_id("GAME01", "token-1") == "p1"
    assert fixture.notifier.notifications == [
        ("GAME01", [PlayerJoined(player_id="p1", player_name="Ana")])
    ]


async def test_create_game_builds_the_rules_from_the_settings(fixture: Fixture) -> None:
    settings = GameSettings(starting_money=2500, salary=120, rent_percent=50)

    await fixture.service.create_game("Ana", seats=2, settings=settings)

    rules = fixture.repository.games["GAME01"].rules
    assert (rules.starting_money, rules.salary, rules.rent_percent) == (2500, 120, 50)


async def test_create_game_uses_the_default_rules_without_settings(fixture: Fixture) -> None:
    await fixture.service.create_game("Ana", seats=2)

    assert fixture.repository.games["GAME01"].rules == GameRules()


async def test_create_game_rejects_settings_out_of_bounds(fixture: Fixture) -> None:
    settings = GameSettings(starting_money=1, salary=50, rent_percent=100)

    with pytest.raises(InvalidGameSettingsError):
        await fixture.service.create_game("Ana", seats=2, settings=settings)

    assert fixture.repository.games == {}


async def test_create_game_draws_a_new_code_until_it_is_free() -> None:
    fixture = Fixture(codes=("GAME01", "GAME01", "GAME02"))
    await fixture.service.create_game("Ana", seats=2)

    joined = await fixture.service.create_game("Bob", seats=2)

    assert joined.code == "GAME02"


@pytest.mark.parametrize(
    ("name", "seats", "error"),
    [("Ana", 5, InvalidSeatCountError), ("  ", 2, InvalidPlayerNameError)],
)
async def test_create_game_with_invalid_input_saves_and_notifies_nothing(
    fixture: Fixture, name: str, seats: int, error: type[Exception]
) -> None:
    with pytest.raises(error):
        await fixture.service.create_game(name, seats=seats)

    assert fixture.repository.games == {}
    assert fixture.notifier.notifications == []


async def test_join_game_seats_the_player_and_starts_the_game_when_full(
    fixture: Fixture,
) -> None:
    await fixture.service.create_game("Ana", seats=2)

    joined = await fixture.service.join_game("GAME01", "Bob")

    assert joined == JoinedGame(code="GAME01", player_id="p2", player_token="token-2")
    assert fixture.repository.games["GAME01"].status is GameStatus.IN_PROGRESS
    assert fixture.registry.find_player_id("GAME01", "token-2") == "p2"
    assert fixture.notifier.notifications[-1] == (
        "GAME01",
        [PlayerJoined(player_id="p2", player_name="Bob"), GameStarted()],
    )


async def test_join_an_unknown_game_fails(fixture: Fixture) -> None:
    with pytest.raises(GameNotFoundError):
        await fixture.service.join_game("NOPE00", "Bob")


async def test_join_a_started_game_fails_without_notifying(fixture: Fixture) -> None:
    await fixture.service.create_game("Ana", seats=2)
    await fixture.service.join_game("GAME01", "Bob")
    notifications_before = len(fixture.notifier.notifications)

    with pytest.raises(GameAlreadyStartedError):
        await fixture.service.join_game("GAME01", "Cleo")

    assert len(fixture.notifier.notifications) == notifications_before


async def test_play_turn_rolls_the_die_and_notifies_the_events(fixture: Fixture) -> None:
    await fixture.service.create_game("Ana", seats=2)
    await fixture.service.join_game("GAME01", "Bob")

    result = await fixture.service.play_turn("GAME01", "token-1")

    expected_events: list[GameEvent] = [
        DiceRolled(player_id="p1", value=3),
        PlayerMoved(player_id="p1", from_position=0, to_position=3),
        PropertyBought(player_id="p1", square_index=3, price=80),
        TurnPassed(player_id="p2"),
    ]
    assert fixture.dice.faces_asked == [6]
    assert result.events == expected_events
    assert result.game is fixture.repository.games["GAME01"]
    assert result.game.current_player is not None
    assert result.game.current_player.id == "p2"
    assert fixture.notifier.notifications[-1] == ("GAME01", expected_events)


async def test_play_turn_on_an_unknown_game_fails(fixture: Fixture) -> None:
    with pytest.raises(GameNotFoundError):
        await fixture.service.play_turn("NOPE00", "token-1")


async def test_play_turn_with_an_unknown_token_fails(fixture: Fixture) -> None:
    await fixture.service.create_game("Ana", seats=2)
    await fixture.service.join_game("GAME01", "Bob")

    with pytest.raises(InvalidPlayerTokenError):
        await fixture.service.play_turn("GAME01", "forged")


async def test_play_turn_out_of_turn_fails_without_notifying(fixture: Fixture) -> None:
    await fixture.service.create_game("Ana", seats=2)
    await fixture.service.join_game("GAME01", "Bob")
    notifications_before = len(fixture.notifier.notifications)

    with pytest.raises(NotYourTurnError):
        await fixture.service.play_turn("GAME01", "token-2")

    assert len(fixture.notifier.notifications) == notifications_before


async def test_get_game_returns_the_saved_game_or_fails(fixture: Fixture) -> None:
    await fixture.service.create_game("Ana", seats=2)

    assert fixture.service.get_game("GAME01").code == "GAME01"
    with pytest.raises(GameNotFoundError):
        fixture.service.get_game("NOPE00")
