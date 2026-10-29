import pytest
from fastapi.testclient import TestClient

from monopoly.main import create_app


class FixedDice:
    def __init__(self, value: int) -> None:
        self._value = value

    def roll(self, faces: int) -> int:
        return self._value


@pytest.fixture
def client() -> TestClient:
    # Rolling 3 from Start lands on Rue Wellington (price 80), an unowned property.
    return TestClient(create_app(dice=FixedDice(3)))
