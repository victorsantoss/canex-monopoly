from monopoly.domain.game import Game


class InMemoryGameRepository:
    def __init__(self) -> None:
        self._games: dict[str, Game] = {}

    def get(self, code: str) -> Game | None:
        return self._games.get(code)

    def save(self, game: Game) -> None:
        self._games[game.code] = game
