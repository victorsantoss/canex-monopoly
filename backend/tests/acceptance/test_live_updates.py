from fastapi.testclient import TestClient


def start_two_player_game(client: TestClient) -> tuple[str, str]:
    ana = client.post("/api/games", json={"player_name": "Ana", "seats": 2}).json()
    client.post(f"/api/games/{ana['code']}/players", json={"player_name": "Bob"})
    return ana["code"], ana["player_token"]


def test_every_connected_player_receives_the_new_state_and_its_events(
    client: TestClient,
) -> None:
    code, token = start_two_player_game(client)

    with (
        client.websocket_connect(f"/ws/games/{code}") as ana_socket,
        client.websocket_connect(f"/ws/games/{code}") as bob_socket,
    ):
        ana_socket.receive_json()
        bob_socket.receive_json()

        turn = client.post(f"/api/games/{code}/turns", headers={"X-Player-Token": token}).json()

        expected = {"type": "game_updated", "state": turn["state"], "events": turn["events"]}
        assert ana_socket.receive_json() == expected
        assert bob_socket.receive_json() == expected
    assert turn["events"][0]["type"] == "dice_rolled"
    assert turn["state"]["current_player_id"] == "p2"


def test_connected_players_see_others_join(client: TestClient) -> None:
    ana = client.post("/api/games", json={"player_name": "Ana", "seats": 2}).json()

    with client.websocket_connect(f"/ws/games/{ana['code']}") as socket:
        socket.receive_json()
        client.post(f"/api/games/{ana['code']}/players", json={"player_name": "Bob"})

        message = socket.receive_json()

    assert message["state"]["status"] == "in_progress"
    assert message["events"] == [
        {"type": "player_joined", "player_id": "p2", "player_name": "Bob"},
        {"type": "game_started"},
    ]


def test_a_late_client_receives_the_current_state_on_connection(client: TestClient) -> None:
    code, token = start_two_player_game(client)
    client.post(f"/api/games/{code}/turns", headers={"X-Player-Token": token})
    current_state = client.get(f"/api/games/{code}").json()

    with client.websocket_connect(f"/ws/games/{code}") as socket:
        message = socket.receive_json()

    assert message == {"type": "game_updated", "state": current_state, "events": []}
