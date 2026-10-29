import pytest
from fastapi.testclient import TestClient


def create_game(client: TestClient, body: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/games", json={"player_name": "Ana", "seats": 2, **body})
    assert response.status_code == 201
    code = response.json()["code"]
    client.post(f"/api/games/{code}/players", json={"player_name": "Bob"})
    state: dict[str, object] = client.get(f"/api/games/{code}").json()
    return state


def test_a_game_created_without_settings_uses_the_defaults(client: TestClient) -> None:
    state = create_game(client, {})

    assert state["settings"] == {"starting_money": 1000, "salary": 50, "rent_percent": 100}
    players = state["players"]
    assert isinstance(players, list)
    assert [player["money"] for player in players] == [1000, 1000]
    board = state["board"]
    assert isinstance(board, list)
    assert board[1]["price"] == 60
    assert board[1]["rent"] == 60


def test_a_game_created_with_settings_uses_them_and_shows_them(client: TestClient) -> None:
    settings = {"starting_money": 2500, "salary": 120, "rent_percent": 50}

    state = create_game(client, {"settings": settings})

    assert state["settings"] == settings
    players = state["players"]
    assert isinstance(players, list)
    assert [player["money"] for player in players] == [2500, 2500]
    board = state["board"]
    assert isinstance(board, list)
    assert board[1]["rent"] == 30


def test_missing_settings_fields_fall_back_to_the_defaults(client: TestClient) -> None:
    state = create_game(client, {"settings": {"salary": 0}})

    assert state["settings"] == {"starting_money": 1000, "salary": 0, "rent_percent": 100}


@pytest.mark.parametrize(
    "settings",
    [
        {"starting_money": 99},
        {"starting_money": 10001},
        {"salary": -1},
        {"salary": 1001},
        {"rent_percent": 9},
        {"rent_percent": 201},
        {"salary": "lots"},
    ],
)
def test_settings_out_of_bounds_are_rejected(
    client: TestClient, settings: dict[str, object]
) -> None:
    response = client.post(
        "/api/games", json={"player_name": "Ana", "seats": 2, "settings": settings}
    )

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)
