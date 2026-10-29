from collections.abc import Mapping

from fastapi import WebSocket


class WebSocketHub:
    """Keeps the open WebSockets of each game in memory and pushes messages to them."""

    def __init__(self) -> None:
        self._sockets_by_game: dict[str, set[WebSocket]] = {}

    async def connect(self, code: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._sockets_by_game.setdefault(code, set()).add(websocket)

    def disconnect(self, code: str, websocket: WebSocket) -> None:
        sockets = self._sockets_by_game.get(code)
        if sockets is None:
            return
        sockets.discard(websocket)
        if not sockets:
            del self._sockets_by_game[code]

    async def broadcast(self, code: str, message: Mapping[str, object]) -> None:
        # Iterate over a copy: dropping a dead socket mutates the set.
        for websocket in list(self._sockets_by_game.get(code, ())):
            try:
                await websocket.send_json(message)
            except Exception:
                # A dead socket must not cost the other players their update; the client
                # gets the full state again when it reconnects.
                self.disconnect(code, websocket)

    def connection_count(self, code: str) -> int:
        return len(self._sockets_by_game.get(code, ()))
