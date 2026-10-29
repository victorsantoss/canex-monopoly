import json

import pytest

from monopoly.adapters.presenter import event_to_json, game_to_json, game_updated_message
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
from monopoly.domain.game import Game


def started_game() -> Game:
    game = Game.create(code="GAME01", seats=2)
    game.join("Ana")
    game.join("Bob")
    return game


def test_waiting_game_state() -> None:
    game = Game.create(code="GAME01", seats=3)
    game.join("Ana")

    state = game_to_json(game)

    assert state["code"] == "GAME01"
    assert state["status"] == "waiting"
    assert state["seats"] == 3
    assert state["current_player_id"] is None
    assert state["winner_id"] is None
    assert state["players"] == [
        {"id": "p1", "name": "Ana", "money": 1500, "position": 0, "is_bankrupt": False}
    ]


def test_board_squares_carry_kind_price_rent_and_owner() -> None:
    game = started_game()
    game.play_turn("p1", 1)

    board = game_to_json(game)["board"]

    assert isinstance(board, list)
    assert len(board) == 16
    assert board[0] == {
        "index": 0,
        "kind": "start",
        "name": "Start",
        "price": None,
        "rent": None,
        "owner_id": None,
    }
    assert board[1] == {
        "index": 1,
        "kind": "property",
        "name": "Rue Ontario",
        "price": 60,
        "rent": 30,
        "owner_id": "p1",
    }
    assert board[2] == {
        "index": 2,
        "kind": "empty",
        "name": "Empty lot",
        "price": None,
        "rent": None,
        "owner_id": None,
    }


def test_in_progress_state_names_the_current_player() -> None:
    game = started_game()
    game.play_turn("p1", 2)

    state = game_to_json(game)

    assert state["status"] == "in_progress"
    assert state["current_player_id"] == "p2"


@pytest.mark.parametrize(
    ("event", "expected"),
    [
        (
            PlayerJoined(player_id="p1", player_name="Ana"),
            {"type": "player_joined", "player_id": "p1", "player_name": "Ana"},
        ),
        (GameStarted(), {"type": "game_started"}),
        (
            DiceRolled(player_id="p1", value=4),
            {"type": "dice_rolled", "player_id": "p1", "value": 4},
        ),
        (
            PlayerMoved(player_id="p1", from_position=14, to_position=2),
            {"type": "player_moved", "player_id": "p1", "from_position": 14, "to_position": 2},
        ),
        (
            SalaryReceived(player_id="p1", amount=200),
            {"type": "salary_received", "player_id": "p1", "amount": 200},
        ),
        (
            PropertyBought(player_id="p1", square_index=3, price=80),
            {"type": "property_bought", "player_id": "p1", "square_index": 3, "price": 80},
        ),
        (
            PropertyUnaffordable(player_id="p1", square_index=3),
            {"type": "property_unaffordable", "player_id": "p1", "square_index": 3},
        ),
        (
            RentPaid(player_id="p2", owner_id="p1", square_index=3, amount=40),
            {
                "type": "rent_paid",
                "player_id": "p2",
                "owner_id": "p1",
                "square_index": 3,
                "amount": 40,
            },
        ),
        (
            PlayerBankrupted(player_id="p2", creditor_id="p1"),
            {"type": "player_bankrupted", "player_id": "p2", "creditor_id": "p1"},
        ),
        (TurnPassed(player_id="p2"), {"type": "turn_passed", "player_id": "p2"}),
        (GameWon(player_id="p1"), {"type": "game_won", "player_id": "p1"}),
    ],
)
def test_every_event_type(event: GameEvent, expected: dict[str, object]) -> None:
    assert event_to_json(event) == expected


def test_game_updated_message_carries_state_and_events() -> None:
    game = started_game()
    events = game.play_turn("p1", 3)

    message = game_updated_message(game, events)

    assert message["type"] == "game_updated"
    assert message["state"] == game_to_json(game)
    assert message["events"] == [event_to_json(event) for event in events]
    json.dumps(message)


def test_state_never_mentions_tokens() -> None:
    serialized = json.dumps(game_to_json(started_game()))

    assert "token" not in serialized
