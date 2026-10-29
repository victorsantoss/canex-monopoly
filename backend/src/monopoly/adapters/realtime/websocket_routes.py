from collections.abc import Awaitable, Callable, Mapping

from fastapi import APIRouter, WebSocket

from monopoly.adapters.realtime.websocket_hub import WebSocketHub

SnapshotProvider = Callable[[str], Awaitable[Mapping[str, object] | None]]

UNKNOWN_GAME_CLOSE_CODE = 4404
TOO_MANY_CONNECTIONS_CLOSE_CODE = 4429


def create_websocket_router(hub: WebSocketHub, snapshot_provider: SnapshotProvider) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws/games/{code}")
    async def game_updates(websocket: WebSocket, code: str) -> None:
        # Register before reading the snapshot so no update slips in between; accept before closing,
        # or browsers see a failed handshake instead of the 4404 code.
        if not await hub.connect(code, websocket):
            await websocket.close(code=TOO_MANY_CONNECTIONS_CLOSE_CODE)
            return
        try:
            snapshot = await snapshot_provider(code)
            if snapshot is None:
                await websocket.close(code=UNKNOWN_GAME_CLOSE_CODE)
                return
            await websocket.send_json(snapshot)
            # Server-to-client only: client messages are read just to notice the disconnection.
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    break
        finally:
            hub.disconnect(code, websocket)

    return router
