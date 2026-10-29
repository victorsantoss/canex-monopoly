from collections.abc import Awaitable, Callable, Mapping

from fastapi import APIRouter, WebSocket

from monopoly.adapters.realtime.websocket_hub import WebSocketHub

SnapshotProvider = Callable[[str], Awaitable[Mapping[str, object] | None]]

UNKNOWN_GAME_CLOSE_CODE = 4404


def create_websocket_router(hub: WebSocketHub, snapshot_provider: SnapshotProvider) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws/games/{code}")
    async def game_updates(websocket: WebSocket, code: str) -> None:
        # Registering before reading the snapshot means no update can slip in between the two;
        # at worst a client sees an update before an equally fresh snapshot, which is harmless
        # since both carry the full state. Accepting before closing also matters: a close during
        # the handshake reaches browsers as a failed connection and the 4404 code is lost.
        await hub.connect(code, websocket)
        try:
            snapshot = await snapshot_provider(code)
            if snapshot is None:
                await websocket.close(code=UNKNOWN_GAME_CLOSE_CODE)
                return
            await websocket.send_json(snapshot)
            # The channel is server to client only: client messages are read and ignored,
            # just to notice the disconnection.
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    break
        finally:
            hub.disconnect(code, websocket)

    return router
