import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from monopoly.adapters.http.error_handlers import ERROR_STATUS, install_error_handlers
from monopoly.application.errors import GameNotFoundError, InvalidPlayerTokenError
from monopoly.domain.errors import (
    GameAlreadyStartedError,
    GameError,
    GameNotInProgressError,
    InvalidGameSettingsError,
    InvalidPlayerNameError,
    InvalidRollError,
    InvalidSeatCountError,
    NotYourTurnError,
    UnknownPlayerError,
)


class Body(BaseModel):
    seats: int


def build_client(error: Exception) -> TestClient:
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/raise")
    async def raise_error() -> None:
        raise error

    @app.post("/validate")
    async def validate(body: Body) -> None:
        return None

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (InvalidPlayerTokenError("bad token"), 401),
        (NotYourTurnError("bad turn"), 403),
        (GameNotFoundError("no game"), 404),
        (GameAlreadyStartedError("started"), 409),
        (GameNotInProgressError("not in progress"), 409),
        (InvalidSeatCountError("seats"), 422),
        (InvalidPlayerNameError("name"), 422),
        (InvalidGameSettingsError("settings"), 422),
    ],
)
def test_errors_map_to_their_status_with_a_detail_message(
    error: Exception, status_code: int
) -> None:
    response = build_client(error).get("/raise")

    assert response.status_code == status_code
    assert response.json() == {"detail": str(error)}


def test_request_validation_errors_are_422_with_a_string_detail() -> None:
    response = build_client(GameNotFoundError()).post("/validate", json={"seats": "many"})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, str)
    assert "seats" in detail


def all_subclasses(base: type[GameError]) -> list[type[GameError]]:
    direct = base.__subclasses__()
    return direct + [nested for child in direct for nested in all_subclasses(child)]


@pytest.mark.parametrize("error", [UnknownPlayerError("p9"), InvalidRollError("roll 7")])
def test_unmapped_game_errors_are_500_with_a_generic_detail(error: GameError) -> None:
    response = build_client(error).get("/raise")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal error"}


@pytest.mark.parametrize("error_type", all_subclasses(GameError))
def test_every_game_error_answers_with_a_json_detail(error_type: type[GameError]) -> None:
    response = build_client(error_type("boom")).get("/raise")

    expected_status = ERROR_STATUS.get(error_type, 500)
    assert response.status_code == expected_status
    assert isinstance(response.json()["detail"], str)
