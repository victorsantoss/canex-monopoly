"""Turns the domain into the JSON shapes of the API contract, for both HTTP and WebSocket."""

from collections.abc import Sequence
from dataclasses import asdict

from monopoly.domain.board import EmptySquare, PropertySquare, Square, StartSquare
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
from monopoly.domain.player import Player

JsonObject = dict[str, object]

EVENT_TYPES: dict[type[GameEvent], str] = {
    PlayerJoined: "player_joined",
    GameStarted: "game_started",
    DiceRolled: "dice_rolled",
    PlayerMoved: "player_moved",
    SalaryReceived: "salary_received",
    PropertyBought: "property_bought",
    PropertyUnaffordable: "property_unaffordable",
    RentPaid: "rent_paid",
    PlayerBankrupted: "player_bankrupted",
    TurnPassed: "turn_passed",
    GameWon: "game_won",
}


def game_to_json(game: Game) -> JsonObject:
    current = game.current_player
    winner = game.winner
    return {
        "code": game.code,
        "status": game.status.value,
        "seats": game.seats,
        "current_player_id": current.id if current else None,
        "winner_id": winner.id if winner else None,
        "board": [
            _square_to_json(index, square, game.owner_of(index))
            for index, square in enumerate(game.board.squares)
        ],
        "players": [_player_to_json(player) for player in game.players],
    }


def event_to_json(event: GameEvent) -> JsonObject:
    # Event fields are named after the contract, so only the discriminator is added.
    return {"type": EVENT_TYPES[type(event)], **asdict(event)}


def game_updated_message(game: Game, events: Sequence[GameEvent]) -> JsonObject:
    return {
        "type": "game_updated",
        "state": game_to_json(game),
        "events": [event_to_json(event) for event in events],
    }


def _square_to_json(index: int, square: Square, owner_id: str | None) -> JsonObject:
    match square:
        case PropertySquare(name=name, price=price, rent=rent):
            return {
                "index": index,
                "kind": "property",
                "name": name,
                "price": price,
                "rent": rent,
                "owner_id": owner_id,
            }
        case StartSquare(name=name):
            kind = "start"
        case EmptySquare(name=name):
            kind = "empty"
    return {
        "index": index,
        "kind": kind,
        "name": name,
        "price": None,
        "rent": None,
        "owner_id": None,
    }


def _player_to_json(player: Player) -> JsonObject:
    return {
        "id": player.id,
        "name": player.name,
        "money": player.money,
        "position": player.position,
        "is_bankrupt": player.is_bankrupt,
    }
