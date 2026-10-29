import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from monopoly.adapters.http.error_handlers import install_error_handlers
from monopoly.application.errors import GameNotFoundError, InvalidPlayerTokenError
from monopoly.domain.errors import (
    GameAlreadyStartedError,
    GameFullError,
    GameNotInProgressError,
    InvalidPlayerNameError,
    InvalidSeatCountError,
    NotYourTurnError,
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

    return TestClient(app)


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (InvalidPlayerTokenError("bad token"), 401),
        (NotYourTurnError("bad turn"), 403),
        (GameNotFoundError("no game"), 404),
        (GameAlreadyStartedError("started"), 409),
        (GameFullError("full"), 409),
        (GameNotInProgressError("not in progress"), 409),
        (InvalidSeatCountError("seats"), 422),
        (InvalidPlayerNameError("name"), 422),
    ],
)
def test_errors_map_to_their_status_with_a_detail_message(
    error: Exception, status_code: int
) -> None:
    response = build_client(error).get("/raise")

    assert response.status_code == status_code
    assert response.json() == {"detail": str(error)}


def test_request_validation_errors_are_422_with_a_string_detail() -> None:
    response = build_client(GameFullError()).post("/validate", json={"seats": "many"})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, str)
    assert "seats" in detail
