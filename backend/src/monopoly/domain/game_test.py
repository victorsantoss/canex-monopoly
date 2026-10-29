from dataclasses import FrozenInstanceError

import pytest

from monopoly.domain.board import STANDARD_BOARD, Board, EmptySquare, PropertySquare, StartSquare
from monopoly.domain.errors import (
    GameAlreadyStartedError,
    GameError,
    GameNotInProgressError,
    InvalidPlayerNameError,
    InvalidRollError,
    InvalidSeatCountError,
    NotYourTurnError,
    UnknownPlayerError,
)
from monopoly.domain.events import (
    DiceRolled,
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
from monopoly.domain.game import Game, GameStatus
from monopoly.domain.rules import GameRules

# Start, a property, an empty lot, another property: small enough to reason about laps.
# At 40% of the price, A rents for 40 and B for 24.
BOARD = Board(
    squares=(
        StartSquare(),
        PropertySquare(name="A", price=100),
        EmptySquare(),
        PropertySquare(name="B", price=60),
    )
)


def new_game(seats: int = 2, starting_money: int = 1000, salary: int = 200) -> Game:
    game = Game(
        code="ABCDEF",
        seats=seats,
        board=BOARD,
        rules=GameRules(starting_money=starting_money, salary=salary, rent_percent=40),
    )
    for name in ["Ana", "Bob", "Cleo", "Dan"][:seats]:
        game.join(name)
    return game


def test_create_returns_a_waiting_game_without_players() -> None:
    game = Game(code="ABCDEF", seats=3)

    assert game.code == "ABCDEF"
    assert game.seats == 3
    assert game.status is GameStatus.WAITING
    assert game.players == ()
    assert game.current_player is None
    assert game.winner is None
    assert game.rules == GameRules()


@pytest.mark.parametrize("seats", [1, 5])
def test_create_rejects_seat_count_outside_rules(seats: int) -> None:
    with pytest.raises(InvalidSeatCountError):
        Game(code="ABCDEF", seats=seats)


@pytest.mark.parametrize("seats", [1, 99])
def test_constructor_rejects_seat_count_outside_rules(seats: int) -> None:
    with pytest.raises(InvalidSeatCountError):
        Game(code="ABCDEF", seats=seats, board=STANDARD_BOARD, rules=GameRules())


def test_players_obtained_from_the_game_cannot_be_mutated() -> None:
    game = new_game()

    with pytest.raises(FrozenInstanceError):
        game.player("p1").money = 0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        game.players[0].position = 3  # type: ignore[misc]
    current = game.current_player
    assert current is not None
    with pytest.raises(FrozenInstanceError):
        current.is_bankrupt = True  # type: ignore[misc]
    assert game.player("p1").money == 1000


def test_name_length_limit_comes_from_the_rules() -> None:
    game = Game(code="ABCDEF", seats=2, rules=GameRules(max_player_name_length=3))

    game.join("Ana")
    with pytest.raises(InvalidPlayerNameError):
        game.join("Bruno")


def test_domain_errors_share_a_base_class() -> None:
    with pytest.raises(GameError):
        Game(code="ABCDEF", seats=9)


def test_join_assigns_ids_in_order_with_starting_money() -> None:
    game = Game(code="ABCDEF", seats=3, rules=GameRules(starting_money=700))

    ana, ana_events = game.join("Ana")
    bob, _ = game.join("Bob")

    assert (ana.id, ana.name, ana.money, ana.position, ana.is_bankrupt) == (
        "p1",
        "Ana",
        700,
        0,
        False,
    )
    assert bob.id == "p2"
    assert ana_events == [PlayerJoined(player_id="p1", player_name="Ana")]
    assert game.status is GameStatus.WAITING
    assert game.current_player is None


def test_join_trims_the_name() -> None:
    game = Game(code="ABCDEF", seats=2)

    player, _ = game.join("  Ana  ")

    assert player.name == "Ana"


@pytest.mark.parametrize("name", ["", "   ", "x" * 21])
def test_join_rejects_invalid_names(name: str) -> None:
    game = Game(code="ABCDEF", seats=2)

    with pytest.raises(InvalidPlayerNameError):
        game.join(name)


def test_join_accepts_a_twenty_character_name() -> None:
    game = Game(code="ABCDEF", seats=2)

    player, _ = game.join("x" * 20)

    assert player.name == "x" * 20


def test_taking_the_last_seat_starts_the_game_with_the_first_player_active() -> None:
    game = Game(code="ABCDEF", seats=2)
    game.join("Ana")

    _, events = game.join("Bob")

    assert events == [PlayerJoined(player_id="p2", player_name="Bob"), GameStarted()]
    assert game.status is GameStatus.IN_PROGRESS
    assert game.current_player is not None
    assert game.current_player.id == "p1"


def test_join_after_the_game_started_is_rejected() -> None:
    game = new_game(seats=2)

    with pytest.raises(GameAlreadyStartedError):
        game.join("Cleo")


def test_player_lookup_raises_for_unknown_ids() -> None:
    game = new_game()

    assert game.player("p2").name == "Bob"
    with pytest.raises(UnknownPlayerError):
        game.player("p9")


def test_play_turn_before_start_is_rejected() -> None:
    game = Game(code="ABCDEF", seats=2)
    game.join("Ana")

    with pytest.raises(GameNotInProgressError):
        game.play_turn("p1", 1)


def test_play_turn_by_an_unknown_player_is_rejected() -> None:
    game = new_game()

    with pytest.raises(UnknownPlayerError):
        game.play_turn("p9", 1)


def test_play_turn_out_of_turn_is_rejected() -> None:
    game = new_game()

    with pytest.raises(NotYourTurnError):
        game.play_turn("p2", 1)


@pytest.mark.parametrize("roll", [0, 7, -1])
def test_play_turn_rejects_a_roll_outside_the_die(roll: int) -> None:
    game = new_game()

    with pytest.raises(InvalidRollError):
        game.play_turn("p1", roll)
    assert game.player("p1").position == 0


def test_play_turn_after_the_game_finished_is_rejected() -> None:
    game = new_game(starting_money=100)
    game.play_turn("p1", 1)  # buys A for 100, money 0
    game.play_turn("p2", 3)  # buys B, money 40
    game.play_turn("p1", 2)  # 1 -> 3, owes 24 with 0: bankrupt

    assert game.status is GameStatus.FINISHED
    with pytest.raises(GameNotInProgressError):
        game.play_turn("p2", 1)


def test_turn_on_an_empty_square_rolls_moves_and_passes() -> None:
    game = new_game()

    events = game.play_turn("p1", 2)

    assert events == [
        DiceRolled(player_id="p1", value=2),
        PlayerMoved(player_id="p1", from_position=0, to_position=2),
        TurnPassed(player_id="p2"),
    ]
    assert game.player("p1").position == 2
    assert game.player("p1").money == 1000


def test_crossing_start_pays_salary_before_the_square_effect() -> None:
    game = new_game()
    game.play_turn("p1", 3)  # buys B
    game.play_turn("p2", 2)

    events = game.play_turn("p1", 2)  # 3 -> 1, crosses Start, buys A

    assert events == [
        DiceRolled(player_id="p1", value=2),
        PlayerMoved(player_id="p1", from_position=3, to_position=1),
        SalaryReceived(player_id="p1", amount=200),
        PropertyBought(player_id="p1", square_index=1, price=100),
        TurnPassed(player_id="p2"),
    ]
    assert game.player("p1").money == 1000 - 60 + 200 - 100


def test_landing_exactly_on_start_pays_salary() -> None:
    game = new_game()
    game.play_turn("p1", 2)
    game.play_turn("p2", 2)

    events = game.play_turn("p1", 2)  # 2 -> 0

    assert SalaryReceived(player_id="p1", amount=200) in events
    assert game.player("p1").position == 0
    assert game.player("p1").money == 1200


def test_salary_helps_pay_the_rent_on_arrival() -> None:
    game = new_game(starting_money=100, salary=50)
    game.play_turn("p1", 1)  # buys A for 100, money 0
    game.play_turn("p2", 2)
    game.play_turn("p1", 1)  # 1 -> 2
    events = game.play_turn("p2", 3)  # 2 -> 1, salary 50, rent 40

    assert RentPaid(player_id="p2", owner_id="p1", square_index=1, amount=40) in events
    assert game.player("p2").money == 100 + 50 - 40
    assert not game.player("p2").is_bankrupt


def test_buying_with_exactly_all_money_is_allowed() -> None:
    game = new_game(starting_money=100)

    events = game.play_turn("p1", 1)

    assert PropertyBought(player_id="p1", square_index=1, price=100) in events
    assert game.player("p1").money == 0
    assert game.owner_of(1) == "p1"


def test_unaffordable_property_stays_with_the_bank() -> None:
    game = new_game(starting_money=99)

    events = game.play_turn("p1", 1)

    assert PropertyUnaffordable(player_id="p1", square_index=1) in events
    assert game.player("p1").money == 99
    assert game.owner_of(1) is None


def test_rent_moves_money_from_visitor_to_owner() -> None:
    game = new_game()
    game.play_turn("p1", 1)

    events = game.play_turn("p2", 1)

    assert events == [
        DiceRolled(player_id="p2", value=1),
        PlayerMoved(player_id="p2", from_position=0, to_position=1),
        RentPaid(player_id="p2", owner_id="p1", square_index=1, amount=40),
        TurnPassed(player_id="p1"),
    ]
    assert game.player("p2").money == 960
    assert game.player("p1").money == 940


def test_rent_exactly_equal_to_money_leaves_zero_and_no_bankruptcy() -> None:
    game = new_game(starting_money=100, salary=0)
    game.play_turn("p1", 1)  # buys A for 100, money 0
    game.play_turn("p2", 3)  # buys B for 60, money 40

    game.play_turn("p1", 1)  # 1 -> 2
    events = game.play_turn("p2", 2)  # 3 -> 1, rent 40 with exactly 40

    assert RentPaid(player_id="p2", owner_id="p1", square_index=1, amount=40) in events
    assert game.player("p2").money == 0
    assert not game.player("p2").is_bankrupt
    assert game.status is GameStatus.IN_PROGRESS


def test_landing_on_own_property_has_no_effect() -> None:
    game = new_game()
    game.play_turn("p1", 1)
    game.play_turn("p2", 2)

    events = game.play_turn("p1", 4)

    assert events == [
        DiceRolled(player_id="p1", value=4),
        PlayerMoved(player_id="p1", from_position=1, to_position=1),
        SalaryReceived(player_id="p1", amount=200),
        TurnPassed(player_id="p2"),
    ]
    assert game.player("p1").money == 1000 - 100 + 200
    assert game.owner_of(1) == "p1"


def test_bankruptcy_pays_the_rest_frees_properties_and_skips_the_player() -> None:
    game = new_game(seats=3, starting_money=100, salary=0)
    game.play_turn("p1", 3)  # p1 buys B (rent 24), money 40
    game.play_turn("p2", 1)  # p2 buys A (rent 40), money 0
    game.play_turn("p3", 2)  # p3 on the empty lot

    game.play_turn("p1", 3)  # 3 -> 2, empty lot
    events = game.play_turn("p2", 2)  # 1 -> 3, owes 24 with 0: bankrupt

    assert events == [
        DiceRolled(player_id="p2", value=2),
        PlayerMoved(player_id="p2", from_position=1, to_position=3),
        RentPaid(player_id="p2", owner_id="p1", square_index=3, amount=0),
        PlayerBankrupted(player_id="p2", creditor_id="p1"),
        TurnPassed(player_id="p3"),
    ]
    assert game.player("p2").is_bankrupt
    assert game.player("p2").money == 0
    assert game.owner_of(1) is None
    assert game.owner_of(3) == "p1"

    game.play_turn("p3", 2)  # 2 -> 0
    events = game.play_turn("p1", 1)  # 2 -> 3, own property; p2 is skipped
    assert events[-1] == TurnPassed(player_id="p3")


def test_partial_rent_gives_the_owner_everything_left() -> None:
    game = new_game(starting_money=120, salary=0)
    game.play_turn("p1", 1)  # p1 buys A (rent 40), money 20
    game.play_turn("p2", 3)  # p2 buys B, money 60
    game.play_turn("p1", 1)  # 1 -> 2
    game.play_turn("p2", 2)  # 3 -> 1, pays 40: p2 has 20, p1 has 60
    game.play_turn("p1", 2)  # 2 -> 0

    events = game.play_turn("p2", 4)  # full lap back on A, owes 40 with 20

    assert RentPaid(player_id="p2", owner_id="p1", square_index=1, amount=20) in events
    assert PlayerBankrupted(player_id="p2", creditor_id="p1") in events
    assert game.player("p1").money == 80
    assert game.player("p2").money == 0
    assert game.owner_of(3) is None


def test_last_player_standing_wins() -> None:
    game = new_game(starting_money=100, salary=0)
    game.play_turn("p1", 1)  # buys A for 100, money 0
    game.play_turn("p2", 3)  # buys B for 60, money 40

    events = game.play_turn("p1", 2)  # 1 -> 3, owes 24 with 0

    assert events[-2:] == [
        PlayerBankrupted(player_id="p1", creditor_id="p2"),
        GameWon(player_id="p2"),
    ]
    assert game.status is GameStatus.FINISHED
    assert game.current_player is None
    assert game.winner is not None
    assert game.winner.id == "p2"
    assert game.owner_of(1) is None


def test_players_are_exposed_in_turn_order() -> None:
    game = new_game(seats=3)

    assert [player.id for player in game.players] == ["p1", "p2", "p3"]
