import hmac


class InMemorySeatRegistry:
    def __init__(self) -> None:
        self._tokens_by_game: dict[str, dict[str, str]] = {}

    def register(self, code: str, player_id: str, token: str) -> None:
        self._tokens_by_game.setdefault(code, {})[player_id] = token

    def find_player_id(self, code: str, token: str) -> str | None:
        # Constant-time comparison so response timing does not leak how much of a token matched.
        for player_id, expected in self._tokens_by_game.get(code, {}).items():
            if hmac.compare_digest(expected.encode(), token.encode()):
                return player_id
        return None
