from collections.abc import Mapping
from typing import cast

from fastapi import WebSocket

from monopoly.adapters.realtime.websocket_hub import WebSocketHub

MESSAGE: Mapping[str, object] = {"type": "game_updated", "state": {}, "events": []}


class FakeWebSocket:
    def __init__(self, *, fails_on_send: bool = False) -> None:
        self.accepted = False
        self.received: list[Mapping[str, object]] = []
        self._fails_on_send = fails_on_send

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: Mapping[str, object]) -> None:
        if self._fails_on_send:
            raise RuntimeError("socket is closed")
        self.received.append(data)

    def as_websocket(self) -> WebSocket:
        return cast(WebSocket, self)


async def test_connect_accepts_and_registers_the_socket() -> None:
    hub = WebSocketHub()
    socket = FakeWebSocket()

    await hub.connect("ABC123", socket.as_websocket())

    assert socket.accepted
    assert hub.connection_count("ABC123") == 1


async def test_broadcast_reaches_every_socket_of_the_game_only() -> None:
    hub = WebSocketHub()
    first, second, other_game = FakeWebSocket(), FakeWebSocket(), FakeWebSocket()
    await hub.connect("ABC123", first.as_websocket())
    await hub.connect("ABC123", second.as_websocket())
    await hub.connect("ZZZ999", other_game.as_websocket())

    await hub.broadcast("ABC123", MESSAGE)

    assert first.received == [MESSAGE]
    assert second.received == [MESSAGE]
    assert other_game.received == []


async def test_broadcast_to_a_game_without_sockets_is_a_no_op() -> None:
    hub = WebSocketHub()

    await hub.broadcast("NOBODY", MESSAGE)

    assert hub.connection_count("NOBODY") == 0


async def test_disconnected_socket_no_longer_receives_broadcasts() -> None:
    hub = WebSocketHub()
    leaving, staying = FakeWebSocket(), FakeWebSocket()
    await hub.connect("ABC123", leaving.as_websocket())
    await hub.connect("ABC123", staying.as_websocket())

    hub.disconnect("ABC123", leaving.as_websocket())
    await hub.broadcast("ABC123", MESSAGE)

    assert leaving.received == []
    assert staying.received == [MESSAGE]


async def test_disconnecting_an_unregistered_socket_is_harmless() -> None:
    hub = WebSocketHub()

    hub.disconnect("ABC123", FakeWebSocket().as_websocket())

    assert hub.connection_count("ABC123") == 0


async def test_failing_socket_is_dropped_and_others_still_receive() -> None:
    hub = WebSocketHub()
    broken, healthy = FakeWebSocket(fails_on_send=True), FakeWebSocket()
    await hub.connect("ABC123", broken.as_websocket())
    await hub.connect("ABC123", healthy.as_websocket())

    await hub.broadcast("ABC123", MESSAGE)

    assert healthy.received == [MESSAGE]
    assert hub.connection_count("ABC123") == 1


async def test_last_socket_leaving_empties_the_game() -> None:
    hub = WebSocketHub()
    socket = FakeWebSocket()
    await hub.connect("ABC123", socket.as_websocket())

    hub.disconnect("ABC123", socket.as_websocket())

    assert hub.connection_count("ABC123") == 0
