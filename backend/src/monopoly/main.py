"""Composition root: the only place that wires adapters into the use cases."""

from collections.abc import Mapping

from fastapi import FastAPI

from monopoly.adapters.http.error_handlers import install_error_handlers
from monopoly.adapters.http.game_routes import create_game_router
from monopoly.adapters.persistence.in_memory_game_repository import InMemoryGameRepository
from monopoly.adapters.persistence.in_memory_seat_registry import InMemorySeatRegistry
from monopoly.adapters.presenter import game_updated_message
from monopoly.adapters.randomness import SecureCodeGenerator, SecureDice, SecureTokenGenerator
from monopoly.adapters.realtime.websocket_hub import WebSocketHub
from monopoly.adapters.realtime.websocket_notifier import WebSocketGameNotifier
from monopoly.adapters.realtime.websocket_routes import create_websocket_router
from monopoly.application.errors import GameNotFoundError
from monopoly.application.game_service import GameService
from monopoly.application.ports import Dice


def create_app(dice: Dice | None = None) -> FastAPI:
    app = FastAPI(title="Monopoly")
    hub = WebSocketHub()
    service = GameService(
        repository=InMemoryGameRepository(),
        seats=InMemorySeatRegistry(),
        notifier=WebSocketGameNotifier(hub),
        dice=dice or SecureDice(),
        codes=SecureCodeGenerator(),
        tokens=SecureTokenGenerator(),
    )

    async def snapshot_of(code: str) -> Mapping[str, object] | None:
        try:
            return game_updated_message(service.get_game(code), [])
        except GameNotFoundError:
            return None

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    install_error_handlers(app)
    app.include_router(create_game_router(service))
    app.include_router(create_websocket_router(hub, snapshot_of))
    return app


app = create_app()
