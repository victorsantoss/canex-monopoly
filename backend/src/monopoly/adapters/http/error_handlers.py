from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from monopoly.application.errors import GameNotFoundError, InvalidPlayerTokenError
from monopoly.domain.errors import (
    GameAlreadyStartedError,
    GameNotInProgressError,
    InvalidGameSettingsError,
    InvalidPlayerNameError,
    InvalidSeatCountError,
    NotYourTurnError,
)

ERROR_STATUS: dict[type[Exception], int] = {
    InvalidPlayerTokenError: HTTPStatus.UNAUTHORIZED,
    NotYourTurnError: HTTPStatus.FORBIDDEN,
    GameNotFoundError: HTTPStatus.NOT_FOUND,
    GameAlreadyStartedError: HTTPStatus.CONFLICT,
    GameNotInProgressError: HTTPStatus.CONFLICT,
    InvalidSeatCountError: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidPlayerNameError: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidGameSettingsError: HTTPStatus.UNPROCESSABLE_ENTITY,
}


def install_error_handlers(app: FastAPI) -> None:
    async def handle_known_error(request: Request, error: Exception) -> JSONResponse:
        return JSONResponse(status_code=ERROR_STATUS[type(error)], content={"detail": str(error)})

    async def handle_validation_error(request: Request, error: Exception) -> JSONResponse:
        # The contract promises a string `detail`, where FastAPI would send a list of errors.
        assert isinstance(error, RequestValidationError)
        messages = [
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in error.errors()
        ]
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            content={"detail": "; ".join(messages)},
        )

    for error_type in ERROR_STATUS:
        app.add_exception_handler(error_type, handle_known_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
