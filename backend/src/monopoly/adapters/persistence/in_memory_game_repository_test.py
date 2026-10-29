from monopoly.adapters.persistence.in_memory_game_repository import InMemoryGameRepository
from monopoly.domain.game import Game


def test_returns_a_saved_game_by_code_and_none_otherwise() -> None:
    repository = InMemoryGameRepository()
    game = Game.create(code="GAME01", seats=2)

    repository.save(game)

    assert repository.get("GAME01") is game
    assert repository.get("GAME02") is None
