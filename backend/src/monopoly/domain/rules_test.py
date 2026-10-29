import pytest

from monopoly.domain.errors import GameError, InvalidGameSettingsError
from monopoly.domain.rules import GameRules


def test_default_economy() -> None:
    rules = GameRules()

    assert (rules.starting_money, rules.salary, rules.rent_percent) == (1000, 50, 100)


def test_player_names_are_limited_to_20_characters_by_default() -> None:
    assert GameRules().max_player_name_length == 20


@pytest.mark.parametrize(
    ("rent_percent", "price", "rent"),
    [(100, 60, 60), (50, 60, 30), (200, 350, 700), (10, 60, 6), (33, 100, 33), (15, 70, 10)],
)
def test_rent_is_a_percentage_of_the_price_rounded_down(
    rent_percent: int, price: int, rent: int
) -> None:
    assert GameRules(rent_percent=rent_percent).rent_for(price) == rent


def test_configured_rules_keep_the_chosen_settings() -> None:
    rules = GameRules.configured(starting_money=2500, salary=0, rent_percent=200)

    assert rules == GameRules(starting_money=2500, salary=0, rent_percent=200)


@pytest.mark.parametrize(
    ("starting_money", "salary", "rent_percent"),
    [(100, 0, 10), (10000, 1000, 200)],
)
def test_configured_rules_accept_the_bounds(
    starting_money: int, salary: int, rent_percent: int
) -> None:
    rules = GameRules.configured(
        starting_money=starting_money, salary=salary, rent_percent=rent_percent
    )

    assert (rules.starting_money, rules.salary, rules.rent_percent) == (
        starting_money,
        salary,
        rent_percent,
    )


@pytest.mark.parametrize(
    ("starting_money", "salary", "rent_percent", "field"),
    [
        (99, 50, 100, "Starting money"),
        (10001, 50, 100, "Starting money"),
        (1000, -1, 100, "Salary"),
        (1000, 1001, 100, "Salary"),
        (1000, 50, 9, "Rent percent"),
        (1000, 50, 201, "Rent percent"),
    ],
)
def test_configured_rules_reject_settings_out_of_bounds(
    starting_money: int, salary: int, rent_percent: int, field: str
) -> None:
    with pytest.raises(InvalidGameSettingsError, match=field):
        GameRules.configured(
            starting_money=starting_money, salary=salary, rent_percent=rent_percent
        )


def test_invalid_settings_are_a_domain_error() -> None:
    assert issubclass(InvalidGameSettingsError, GameError)
