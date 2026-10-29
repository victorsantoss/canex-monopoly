"""Plays many games with the domain rules to check that the economy ends games."""

import argparse
import random
import statistics

from monopoly.domain.game import Game, GameStatus
from monopoly.domain.rules import GameRules

PLAYER_NAMES = ["Ana", "Bob", "Cleo", "Dan"]


def play_game(seats: int, rules: GameRules, turn_cap: int, rng: random.Random) -> int | None:
    game = Game(code="SIMULA", seats=seats, rules=rules)
    for name in PLAYER_NAMES[:seats]:
        game.join(name)
    for turn in range(1, turn_cap + 1):
        current = game.current_player
        assert current is not None
        game.play_turn(current.id, rng.randint(1, rules.die_faces))
        if game.status is GameStatus.FINISHED:
            return turn
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=300)
    parser.add_argument("--starting-money", type=int, default=GameRules().starting_money)
    parser.add_argument("--salary", type=int, default=GameRules().salary)
    parser.add_argument("--rent-percent", type=int, default=GameRules().rent_percent)
    parser.add_argument("--turn-cap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    rules = GameRules(
        starting_money=args.starting_money, salary=args.salary, rent_percent=args.rent_percent
    )
    rng = random.Random(args.seed)
    print(
        f"start {rules.starting_money} / salary {rules.salary} / rent {rules.rent_percent}% "
        f"- {args.games} games per player count, cap {args.turn_cap} turns"
    )
    for seats in range(rules.min_seats, rules.max_seats + 1):
        lengths = [
            length
            for length in (play_game(seats, rules, args.turn_cap, rng) for _ in range(args.games))
            if length is not None
        ]
        finish_rate = 100 * len(lengths) / args.games
        median = f"{statistics.median(lengths):.0f}" if lengths else "-"
        print(f"{seats} players: {finish_rate:5.1f}% finished, median {median} turns")


if __name__ == "__main__":
    main()
