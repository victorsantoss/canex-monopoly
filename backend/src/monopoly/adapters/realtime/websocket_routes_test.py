from collections.abc import Mapping

import pytest
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from monopoly.adapters.realtime.websocket_hub import WebSocketHub
from monopoly.adapters.realtime.websocket_routes import create_websocket_router

KNOWN_GAMES = frozenset({"ABC123", "ZZZ999"})


def snapshot_message(code: str) -> Mapping[str, object]:
    return {"type": "game_updated", "state": {"code": code, "status": "waiting"}, "events": []}


def update_message(code: str) -> Mapping[str, object]:
    return {
        "type": "game_updated",
        "state": {"code": code, "status": "in_progress"},
        "events": [{"type": "game_started"}],
    }


async def snapshot_of(code: str) -> Mapping[str, object] | None:
    return snapshot_message(code) if code in KNOWN_GAMES else None


def build_client(hub: WebSocketHub) -> TestClient:
    app = FastAPI()
    app.include_router(create_websocket_router(hub, snapshot_of))

    # Broadcasting from an HTTP handler runs it on the app's event loop, as a use case will.
    @app.post("/test/broadcast/{code}")
    async def broadcast(code: str) -> None:
        await hub.broadcast(code, update_message(code))

    return TestClient(app)


def test_connecting_client_receives_the_snapshot_right_away() -> None:
    client = build_client(WebSocketHub())

    with client.websocket_connect("/ws/games/ABC123") as socket:
        assert socket.receive_json() == snapshot_message("ABC123")


def test_unknown_game_is_closed_with_4404() -> None:
    client = build_client(WebSocketHub())

    with (
        pytest.raises(WebSocketDisconnect) as closed,
        client.websocket_connect("/ws/games/NOPE00") as socket,
    ):
        socket.receive_json()

    assert closed.value.code == 4404


def test_clients_of_the_same_game_receive_its_broadcasts_and_no_other() -> None:
    client = build_client(WebSocketHub())

    with (
        client.websocket_connect("/ws/games/ABC123") as first,
        client.websocket_connect("/ws/games/ABC123") as second,
        client.websocket_connect("/ws/games/ZZZ999") as other_game,
    ):
        for socket in (first, second, other_game):
            socket.receive_json()

        client.post("/test/broadcast/ABC123")
        client.post("/test/broadcast/ZZZ999")

        assert first.receive_json() == update_message("ABC123")
        assert second.receive_json() == update_message("ABC123")
        # Its first message after the snapshot is its own game's update, not ABC123's.
        assert other_game.receive_json() == update_message("ZZZ999")


class RecordingHub(WebSocketHub):
    def __init__(self) -> None:
        super().__init__()
        self.disconnected: list[str] = []

    def disconnect(self, code: str, websocket: WebSocket) -> None:
        self.disconnected.append(code)
        super().disconnect(code, websocket)


def test_socket_is_unregistered_when_the_client_disconnects() -> None:
    hub = RecordingHub()
    client = build_client(hub)

    with client.websocket_connect("/ws/games/ABC123") as socket:
        socket.receive_json()
        assert hub.disconnected == []

    assert hub.disconnected == ["ABC123"]
