from dataclasses import dataclass

from monopoly.domain.errors import InvalidGameSettingsError

STARTING_MONEY_BOUNDS = (100, 10_000)
SALARY_BOUNDS = (0, 1_000)
RENT_PERCENT_BOUNDS = (10, 200)


@dataclass(frozen=True)
class GameRules:
    starting_money: int = 1000
    salary: int = 50
    rent_percent: int = 100
    min_seats: int = 2
    max_seats: int = 4
    die_faces: int = 6

    # Bounds only limit what a game creator may choose; tests and simulations build GameRules
    # directly to explore any economy.
    @classmethod
    def configured(cls, *, starting_money: int, salary: int, rent_percent: int) -> "GameRules":
        _check_bounds("Starting money", starting_money, STARTING_MONEY_BOUNDS)
        _check_bounds("Salary", salary, SALARY_BOUNDS)
        _check_bounds("Rent percent", rent_percent, RENT_PERCENT_BOUNDS)
        return cls(starting_money=starting_money, salary=salary, rent_percent=rent_percent)

    def rent_for(self, price: int) -> int:
        return price * self.rent_percent // 100


def _check_bounds(label: str, value: int, bounds: tuple[int, int]) -> None:
    low, high = bounds
    if not low <= value <= high:
        raise InvalidGameSettingsError(f"{label} must be between {low} and {high}, got {value}.")
