"""Acceptance scenarios for the lobby (docs/spec.md, section 4, "Lobby")."""

import string

import pytest
from fastapi.testclient import TestClient

CODE_ALPHABET = set(string.ascii_uppercase + "23456789") - {"O", "I"}


def create_game(client: TestClient, name: str = "Ana", seats: int = 2) -> dict[str, str]:
    response = client.post("/api/games", json={"player_name": name, "seats": seats})
    assert response.status_code == 201
    body: dict[str, str] = response.json()
    return body


def join_game(client: TestClient, code: str, name: str) -> dict[str, str]:
    response = client.post(f"/api/games/{code}/players", json={"player_name": name})
    assert response.status_code == 201
    body: dict[str, str] = response.json()
    return body


def play_turn(client: TestClient, code: str, token: str) -> int:
    response = client.post(f"/api/games/{code}/turns", headers={"X-Player-Token": token})
    return response.status_code


def test_create_a_game_waiting_for_players_with_the_creator_in_the_first_seat(
    client: TestClient,
) -> None:
    joined = create_game(client, "Ana", seats=3)

    assert joined["player_id"] == "p1"
    assert joined["player_token"]
    assert len(joined["code"]) == 6
    assert set(joined["code"]) <= CODE_ALPHABET
    state = client.get(f"/api/games/{joined['code']}").json()
    assert state["code"] == joined["code"]
    assert state["status"] == "waiting"
    assert state["seats"] == 3
    assert state["current_player_id"] is None
    assert state["winner_id"] is None
    assert [player["name"] for player in state["players"]] == ["Ana"]
    assert len(state["board"]) == 16


@pytest.mark.parametrize(
    "body",
    [
        {"player_name": "Ana", "seats": 1},
        {"player_name": "Ana", "seats": 5},
        {"player_name": "   ", "seats": 2},
        {"player_name": "A" * 21, "seats": 2},
        {"seats": 2},
    ],
)
def test_creating_a_game_with_invalid_input_is_rejected(
    client: TestClient, body: dict[str, object]
) -> None:
    response = client.post("/api/games", json=body)

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_players_take_the_next_seats_and_the_last_seat_starts_the_game(
    client: TestClient,
) -> None:
    code = create_game(client, "Ana", seats=3)["code"]

    assert join_game(client, code, "Bob")["player_id"] == "p2"
    assert client.get(f"/api/games/{code}").json()["status"] == "waiting"

    assert join_game(client, code, "Cleo")["player_id"] == "p3"
    state = client.get(f"/api/games/{code}").json()
    assert state["status"] == "in_progress"
    assert state["current_player_id"] == "p1"
    assert [player["id"] for player in state["players"]] == ["p1", "p2", "p3"]


def test_joining_an_unknown_game_is_rejected(client: TestClient) -> None:
    response = client.post("/api/games/ZZZZZZ/players", json={"player_name": "Bob"})

    assert response.status_code == 404
    assert isinstance(response.json()["detail"], str)


def test_joining_a_full_and_started_game_is_rejected(client: TestClient) -> None:
    code = create_game(client, seats=2)["code"]
    join_game(client, code, "Bob")

    response = client.post(f"/api/games/{code}/players", json={"player_name": "Cleo"})

    assert response.status_code == 409


def test_joining_with_an_invalid_name_is_rejected(client: TestClient) -> None:
    code = create_game(client, seats=2)["code"]

    response = client.post(f"/api/games/{code}/players", json={"player_name": ""})

    assert response.status_code == 422


def test_reading_an_unknown_game_is_rejected(client: TestClient) -> None:
    assert client.get("/api/games/ZZZZZZ").status_code == 404


def test_playing_without_a_token_or_with_an_unknown_token_is_rejected(
    client: TestClient,
) -> None:
    code = create_game(client)["code"]
    join_game(client, code, "Bob")

    missing = client.post(f"/api/games/{code}/turns")

    assert missing.status_code == 401
    assert play_turn(client, code, "forged") == 401


def test_a_token_of_another_game_is_rejected(client: TestClient) -> None:
    first = create_game(client)
    join_game(client, first["code"], "Bob")
    other = create_game(client, "Eve")

    assert play_turn(client, first["code"], other["player_token"]) == 401


def test_playing_out_of_turn_is_rejected(client: TestClient) -> None:
    code = create_game(client)["code"]
    bob = join_game(client, code, "Bob")

    assert play_turn(client, code, bob["player_token"]) == 403


def test_playing_before_the_game_starts_is_rejected(client: TestClient) -> None:
    ana = create_game(client)

    assert play_turn(client, ana["code"], ana["player_token"]) == 409


def test_playing_on_an_unknown_game_is_rejected(client: TestClient) -> None:
    assert play_turn(client, "ZZZZZZ", "whatever") == 404


def test_the_active_player_plays_a_turn(client: TestClient) -> None:
    ana = create_game(client)
    join_game(client, ana["code"], "Bob")

    response = client.post(
        f"/api/games/{ana['code']}/turns", headers={"X-Player-Token": ana["player_token"]}
    )

    assert response.status_code == 200
    body = response.json()
    assert [event["type"] for event in body["events"]] == [
        "dice_rolled",
        "player_moved",
        "property_bought",
        "turn_passed",
    ]
    assert body["state"]["current_player_id"] == "p2"
    assert body["state"]["board"][3]["owner_id"] == "p1"
    assert body["state"]["players"][0] == {
        "id": "p1",
        "name": "Ana",
        "money": 1420,
        "position": 3,
        "is_bankrupt": False,
    }
    assert ana["player_token"] not in response.text
