import asyncio
import logging
from collections.abc import Mapping

from fastapi import WebSocket

# Commands await the broadcast, so a client that stops reading must not hold every turn hostage.
SEND_TIMEOUT_SECONDS = 2.0
MAX_SOCKETS_PER_GAME = 16
SEND_FAILURE_CLOSE_CODE = 1011

logger = logging.getLogger(__name__)


class WebSocketHub:
    def __init__(self, *, send_timeout_seconds: float = SEND_TIMEOUT_SECONDS) -> None:
        self._send_timeout_seconds = send_timeout_seconds
        self._sockets_by_game: dict[str, set[WebSocket]] = {}

    async def connect(self, code: str, websocket: WebSocket) -> bool:
        """Accept and subscribe the socket; False when the game is full, for the caller to close."""
        await websocket.accept()
        sockets = self._sockets_by_game.setdefault(code, set())
        if len(sockets) >= MAX_SOCKETS_PER_GAME:
            return False
        sockets.add(websocket)
        return True

    def disconnect(self, code: str, websocket: WebSocket) -> None:
        sockets = self._sockets_by_game.get(code)
        if sockets is None:
            return
        sockets.discard(websocket)
        if not sockets:
            del self._sockets_by_game[code]

    async def broadcast(self, code: str, message: Mapping[str, object]) -> None:
        # Iterate over a copy: dropping a dead socket mutates the set.
        sockets = list(self._sockets_by_game.get(code, ()))
        await asyncio.gather(*(self._send(code, websocket, message) for websocket in sockets))

    async def _send(self, code: str, websocket: WebSocket, message: Mapping[str, object]) -> None:
        try:
            await asyncio.wait_for(websocket.send_json(message), self._send_timeout_seconds)
        except Exception:
            logger.warning("Dropping a socket of game %s: send failed or timed out", code)
            self.disconnect(code, websocket)
            # Closing makes the client reconnect, and every connection starts with a full snapshot.
            try:
                await asyncio.wait_for(
                    websocket.close(code=SEND_FAILURE_CLOSE_CODE), self._send_timeout_seconds
                )
            except Exception:
                logger.debug("Closing a dropped socket of game %s failed", code)
