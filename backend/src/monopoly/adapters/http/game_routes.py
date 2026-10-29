from typing import Annotated

from fastapi import APIRouter, Header, status
from pydantic import BaseModel, Field

from monopoly.adapters.presenter import JsonObject, event_to_json, game_to_json
from monopoly.application.errors import InvalidPlayerTokenError
from monopoly.application.game_service import GameService, JoinedGame
from monopoly.domain.rules import GameRules

DEFAULT_RULES = GameRules()


class GameSettingsRequest(BaseModel):
    starting_money: int = DEFAULT_RULES.starting_money
    salary: int = DEFAULT_RULES.salary
    rent_percent: int = DEFAULT_RULES.rent_percent

    def to_rules(self) -> GameRules:
        return GameRules.configured(
            starting_money=self.starting_money,
            salary=self.salary,
            rent_percent=self.rent_percent,
        )


class CreateGameRequest(BaseModel):
    player_name: str
    seats: int
    settings: GameSettingsRequest = Field(default_factory=GameSettingsRequest)


class JoinGameRequest(BaseModel):
    player_name: str


class JoinedGameResponse(BaseModel):
    code: str
    player_id: str
    player_token: str

    @classmethod
    def of(cls, joined: JoinedGame) -> "JoinedGameResponse":
        return cls(code=joined.code, player_id=joined.player_id, player_token=joined.player_token)


def create_game_router(service: GameService) -> APIRouter:
    # Request models only check JSON types: names, seat counts and settings bounds belong to the
    # domain.
    router = APIRouter(prefix="/api/games")

    @router.post("", status_code=status.HTTP_201_CREATED)
    async def create_game(request: CreateGameRequest) -> JoinedGameResponse:
        joined = await service.create_game(
            request.player_name, request.seats, request.settings.to_rules()
        )
        return JoinedGameResponse.of(joined)

    @router.post("/{code}/players", status_code=status.HTTP_201_CREATED)
    async def join_game(code: str, request: JoinGameRequest) -> JoinedGameResponse:
        return JoinedGameResponse.of(await service.join_game(code, request.player_name))

    @router.get("/{code}")
    async def get_game(code: str) -> JsonObject:
        return game_to_json(service.get_game(code))

    @router.post("/{code}/turns")
    async def play_turn(
        code: str, x_player_token: Annotated[str | None, Header()] = None
    ) -> JsonObject:
        if not x_player_token:
            raise InvalidPlayerTokenError("Missing X-Player-Token header.")
        result = await service.play_turn(code, x_player_token)
        return {
            "state": game_to_json(result.game),
            "events": [event_to_json(event) for event in result.events],
        }

    return router
