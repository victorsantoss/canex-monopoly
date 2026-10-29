from collections.abc import Mapping
from typing import cast

from fastapi import WebSocket

from monopoly.adapters.realtime.websocket_hub import WebSocketHub

MESSAGE: Mapping[str, object] = {"type": "game_updated", "state": {}, "events": []}


class FakeWebSocket:
    def __init__(self, *, fails_on_send: bool = False) -> None:
        self.accepted = False
        self.send_attempts = 0
        self.received: list[Mapping[str, object]] = []
        self._fails_on_send = fails_on_send

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: Mapping[str, object]) -> None:
        self.send_attempts += 1
        if self._fails_on_send:
            raise RuntimeError("socket is closed")
        self.received.append(data)

    def as_websocket(self) -> WebSocket:
        return cast(WebSocket, self)


async def test_connect_accepts_the_socket_and_subscribes_it_to_the_game() -> None:
    hub = WebSocketHub()
    socket = FakeWebSocket()

    await hub.connect("ABC123", socket.as_websocket())
    await hub.broadcast("ABC123", MESSAGE)

    assert socket.accepted
    assert socket.received == [MESSAGE]


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


async def test_broadcast_to_a_game_without_sockets_reaches_nobody() -> None:
    hub = WebSocketHub()
    other_game = FakeWebSocket()
    await hub.connect("ZZZ999", other_game.as_websocket())

    await hub.broadcast("NOBODY", MESSAGE)

    assert other_game.received == []


async def test_disconnected_socket_no_longer_receives_broadcasts() -> None:
    hub = WebSocketHub()
    leaving, staying = FakeWebSocket(), FakeWebSocket()
    await hub.connect("ABC123", leaving.as_websocket())
    await hub.connect("ABC123", staying.as_websocket())

    hub.disconnect("ABC123", leaving.as_websocket())
    await hub.broadcast("ABC123", MESSAGE)

    assert leaving.received == []
    assert staying.received == [MESSAGE]


async def test_disconnecting_an_unregistered_socket_leaves_the_others_subscribed() -> None:
    hub = WebSocketHub()
    registered = FakeWebSocket()
    await hub.connect("ABC123", registered.as_websocket())

    hub.disconnect("ABC123", FakeWebSocket().as_websocket())
    hub.disconnect("NOBODY", FakeWebSocket().as_websocket())
    await hub.broadcast("ABC123", MESSAGE)

    assert registered.received == [MESSAGE]


async def test_failing_socket_is_dropped_and_others_still_receive() -> None:
    hub = WebSocketHub()
    broken, healthy = FakeWebSocket(fails_on_send=True), FakeWebSocket()
    await hub.connect("ABC123", broken.as_websocket())
    await hub.connect("ABC123", healthy.as_websocket())

    await hub.broadcast("ABC123", MESSAGE)
    await hub.broadcast("ABC123", MESSAGE)

    assert healthy.received == [MESSAGE, MESSAGE]
    assert broken.send_attempts == 1


async def test_game_accepts_new_sockets_after_the_last_one_left() -> None:
    hub = WebSocketHub()
    first, later = FakeWebSocket(), FakeWebSocket()
    await hub.connect("ABC123", first.as_websocket())
    hub.disconnect("ABC123", first.as_websocket())

    await hub.connect("ABC123", later.as_websocket())
    await hub.broadcast("ABC123", MESSAGE)

    assert first.received == []
    assert later.received == [MESSAGE]
