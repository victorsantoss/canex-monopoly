from collections.abc import Mapping

from monopoly.adapters.presenter import game_updated_message
from monopoly.adapters.realtime.websocket_hub import WebSocketHub
from monopoly.adapters.realtime.websocket_notifier import WebSocketGameNotifier
from monopoly.domain.game import Game


class RecordingHub(WebSocketHub):
    def __init__(self) -> None:
        super().__init__()
        self.broadcasts: list[tuple[str, Mapping[str, object]]] = []

    async def broadcast(self, code: str, message: Mapping[str, object]) -> None:
        self.broadcasts.append((code, message))


async def test_broadcasts_the_game_updated_message_to_the_game() -> None:
    hub = RecordingHub()
    game = Game.create(code="GAME01", seats=2)
    _, events = game.join("Ana")

    await WebSocketGameNotifier(hub).notify(game, events)

    assert hub.broadcasts == [("GAME01", game_updated_message(game, events))]
