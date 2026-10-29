from monopoly.adapters.persistence.in_memory_seat_registry import InMemorySeatRegistry


def test_finds_the_player_of_a_registered_token() -> None:
    registry = InMemorySeatRegistry()
    registry.register("GAME01", "p1", "token-1")
    registry.register("GAME01", "p2", "token-2")

    assert registry.find_player_id("GAME01", "token-1") == "p1"
    assert registry.find_player_id("GAME01", "token-2") == "p2"


def test_unknown_tokens_and_tokens_of_other_games_are_not_found() -> None:
    registry = InMemorySeatRegistry()
    registry.register("GAME01", "p1", "token-1")

    assert registry.find_player_id("GAME01", "forged") is None
    assert registry.find_player_id("GAME02", "token-1") is None
