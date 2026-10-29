"""Acceptance scenarios for the domain rules (docs/spec.md, section 4, "Domain rules")."""

import pytest
from monopoly.domain.board import STANDARD_BOARD, Board, EmptySquare, PropertySquare, StartSquare
from monopoly.domain.errors import GameNotInProgressError, NotYourTurnError
from monopoly.domain.events import (
    GameWon,
    PlayerBankrupted,
    PropertyUnaffordable,
    RentPaid,
    SalaryReceived,
    TurnPassed,
)
from monopoly.domain.game import Game, GameStatus
from monopoly.domain.rules import GameRules

# A tiny board keeps multi-turn scenarios short: every lap is four squares.
SMALL_BOARD = Board(
    squares=(
        StartSquare(),
        PropertySquare(name="Cheap street", price=50, rent=150),
        PropertySquare(name="Side street", price=10, rent=10),
        EmptySquare(),
    )
)


def start_game(
    seats: int = 2,
    board: Board = STANDARD_BOARD,
    rules: GameRules | None = None,
) -> Game:
    game = Game.create(code="ABCDEF", seats=seats, board=board, rules=rules or GameRules())
    for name in ["Ana", "Bob", "Cleo", "Dan"][:seats]:
        game.join(name)
    return game


def test_move_the_active_player_by_the_roll_wrapping_around_the_board() -> None:
    game = start_game()

    game.play_turn("p1", 3)
    assert game.player("p1").position == 3

    game.play_turn("p2", 2)
    game.play_turn("p1", 6)  # 9
    game.play_turn("p2", 3)
    game.play_turn("p1", 6)  # 15
    game.play_turn("p2", 3)
    game.play_turn("p1", 4)  # wraps to 3

    assert game.player("p1").position == 3


def test_salary_is_paid_when_the_move_crosses_or_ends_on_start() -> None:
    game = start_game(board=SMALL_BOARD, rules=GameRules(starting_money=1000))

    game.play_turn("p1", 3)  # empty lot
    game.play_turn("p2", 3)
    crossing = game.play_turn("p1", 2)  # 3 -> 1, crosses Start, buys for 50
    game.play_turn("p2", 1)  # 3 -> 0, ends on Start

    assert SalaryReceived(player_id="p1", amount=200) in crossing
    assert game.player("p1").money == 1000 + 200 - 50
    assert game.player("p2").money == 1000 + 200


def test_buy_an_unowned_property_with_enough_money() -> None:
    game = start_game()

    game.play_turn("p1", 1)

    assert game.player("p1").money == 1500 - 60
    assert game.owner_of(1) == "p1"


def test_cannot_afford_an_unowned_property_changes_nothing() -> None:
    game = start_game(rules=GameRules(starting_money=50))

    events = game.play_turn("p1", 1)  # priced 60

    assert PropertyUnaffordable(player_id="p1", square_index=1) in events
    assert game.player("p1").money == 50
    assert game.owner_of(1) is None


def test_rent_goes_from_the_player_to_the_owner() -> None:
    game = start_game()
    game.play_turn("p1", 1)  # buys Rue Ontario, rent 30

    events = game.play_turn("p2", 1)

    assert RentPaid(player_id="p2", owner_id="p1", square_index=1, amount=30) in events
    assert game.player("p2").money == 1500 - 30
    assert game.player("p1").money == 1500 - 60 + 30


def test_landing_on_own_property_does_nothing() -> None:
    game = start_game(board=SMALL_BOARD, rules=GameRules(salary=0))
    game.play_turn("p1", 1)  # buys Cheap street
    game.play_turn("p2", 3)
    money_before = game.player("p1").money

    game.play_turn("p1", 4)  # full lap, back on Cheap street

    assert game.player("p1").money == money_before
    assert game.owner_of(1) == "p1"


def test_bankruptcy_pays_what_is_left_eliminates_and_frees_properties() -> None:
    game = start_game(seats=3, board=SMALL_BOARD, rules=GameRules(starting_money=100, salary=0))
    game.play_turn("p1", 1)  # p1 buys Cheap street (rent 150), money 50
    game.play_turn("p2", 2)  # p2 buys Side street, money 90
    game.play_turn("p3", 3)
    game.play_turn("p1", 4)

    events = game.play_turn("p2", 3)  # lands on Cheap street, owes 150 with 90

    assert PlayerBankrupted(player_id="p2", creditor_id="p1") in events
    assert game.player("p1").money == 50 + 90
    assert game.player("p2").money == 0
    assert game.player("p2").is_bankrupt
    assert game.owner_of(2) is None


def test_last_player_standing_wins_and_the_game_is_finished() -> None:
    game = start_game(board=SMALL_BOARD, rules=GameRules(starting_money=100, salary=0))
    game.play_turn("p1", 1)  # p1 buys Cheap street (rent 150)

    events = game.play_turn("p2", 1)

    assert events[-1] == GameWon(player_id="p1")
    assert game.status is GameStatus.FINISHED
    assert game.winner is not None
    assert game.winner.id == "p1"
    assert game.current_player is None


def test_guards_only_the_active_player_plays_and_only_while_in_progress() -> None:
    waiting = Game.create(code="ABCDEF", seats=2)
    waiting.join("Ana")
    with pytest.raises(GameNotInProgressError):
        waiting.play_turn("p1", 1)

    game = start_game(board=SMALL_BOARD, rules=GameRules(starting_money=100, salary=0))
    with pytest.raises(NotYourTurnError):
        game.play_turn("p2", 1)

    game.play_turn("p1", 1)
    game.play_turn("p2", 1)  # bankrupt: game finished
    with pytest.raises(GameNotInProgressError):
        game.play_turn("p1", 1)


def test_turn_passes_to_the_next_non_bankrupt_player() -> None:
    game = start_game(seats=3, board=SMALL_BOARD, rules=GameRules(starting_money=100, salary=0))
    first_turn = game.play_turn("p1", 1)  # p1 buys Cheap street (rent 150)
    assert first_turn[-1] == TurnPassed(player_id="p2")

    game.play_turn("p2", 2)  # p2 buys Side street
    game.play_turn("p3", 3)
    game.play_turn("p1", 4)
    game.play_turn("p2", 3)  # p2 lands on Cheap street and goes bankrupt
    after_p3 = game.play_turn("p3", 3)  # p3 buys Side street, back with the bank

    assert after_p3[-1] == TurnPassed(player_id="p1")
    after_p1 = game.play_turn("p1", 1)  # p1 pays rent to p3 on Side street

    assert after_p1[-1] == TurnPassed(player_id="p3")
    assert game.current_player is not None
    assert game.current_player.id == "p3"
