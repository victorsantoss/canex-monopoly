from collections.abc import Sequence

from monopoly.adapters.presenter import game_updated_message
from monopoly.adapters.realtime.websocket_hub import WebSocketHub
from monopoly.domain.events import GameEvent
from monopoly.domain.game import Game


class WebSocketGameNotifier:
    def __init__(self, hub: WebSocketHub) -> None:
        self._hub = hub

    async def notify(self, game: Game, events: Sequence[GameEvent]) -> None:
        await self._hub.broadcast(game.code, game_updated_message(game, events))
