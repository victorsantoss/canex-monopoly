import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from monopoly.application.errors import GameNotFoundError, InvalidPlayerTokenError
from monopoly.domain.errors import (
    GameAlreadyStartedError,
    GameError,
    GameNotInProgressError,
    InvalidGameSettingsError,
    InvalidPlayerNameError,
    InvalidSeatCountError,
    NotYourTurnError,
)

logger = logging.getLogger(__name__)

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

    # Any GameError without an explicit status is a server bug (e.g. an unknown player id that
    # the service should have rejected earlier); answer it in the documented shape anyway.
    @app.exception_handler(GameError)
    async def handle_unmapped_game_error(request: Request, error: GameError) -> JSONResponse:
        logger.error("Unmapped game error", exc_info=error)
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content={"detail": "Internal error"}
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        # The contract promises a string `detail`, where FastAPI would send a list of errors.
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
