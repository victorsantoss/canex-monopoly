from monopoly.adapters.randomness import (
    CODE_ALPHABET,
    SecureCodeGenerator,
    SecureDice,
    SecureTokenGenerator,
)


def test_code_alphabet_has_no_ambiguous_characters() -> None:
    assert set(CODE_ALPHABET).isdisjoint("01OI")
    assert len(CODE_ALPHABET) == 32


def test_codes_are_six_characters_from_the_alphabet() -> None:
    generator = SecureCodeGenerator()

    for _ in range(200):
        code = generator.new_code()
        assert len(code) == 6
        assert set(code) <= set(CODE_ALPHABET)


def test_dice_rolls_stay_between_one_and_the_number_of_faces() -> None:
    dice = SecureDice()

    rolls = {dice.roll(6) for _ in range(500)}

    assert rolls == {1, 2, 3, 4, 5, 6}


def test_tokens_are_long_and_unique() -> None:
    generator = SecureTokenGenerator()

    tokens = {generator.new_token() for _ in range(100)}

    assert len(tokens) == 100
    assert all(len(token) >= 40 for token in tokens)
