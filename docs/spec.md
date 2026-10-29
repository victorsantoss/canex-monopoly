# Specification

This document is the source of truth for the game behaviour. Every acceptance test in
`backend/tests/acceptance/` maps to a scenario below.

## 1. Rules (as given)

- **Move.** On their turn, the active player rolls a die and moves that many squares on a fixed,
  circular board.
- **Buy or pay.** Some squares are properties with a price and a rent; the others are empty and
  nothing happens there. Landing on an unowned property buys it. Landing on a property owned by
  someone else pays the rent to its owner. Landing on your own property does nothing.
- **Money.** Everyone starts with the same amount. Passing Start pays a salary. A player who cannot
  pay a rent goes bankrupt and is eliminated. The last player standing wins.
- **Multiplayer.** A player creates a game for 2 to 4 players; the others join from their own
  browser with a link and a game code. Everyone sees the game update live.

## 2. Game constants

| Constant        | Default          | Creator may choose |
|-----------------|------------------|--------------------|
| Board size      | 16 squares       | -                  |
| Starting money  | 1000             | 100 to 10000       |
| Salary          | 50               | 0 to 1000          |
| Rent            | 100% of the price | 10% to 200%       |
| Die             | one six-sided die (1-6) | -           |
| Seats           | -                | 2 to 4             |

Rent is rounded down. The board layout (names and prices) lives in
`backend/src/monopoly/domain/board.py` (`STANDARD_BOARD`); the defaults and bounds live in
`backend/src/monopoly/domain/rules.py`.

### Economy check

`backend/scripts/simulate_games.py` plays games with the domain rules and a seeded random die,
and reports, per player count, how many finish within a turn cap and their median length. Run it
from `backend/` with the virtualenv active: `python scripts/simulate_games.py --help`.

300 games per player count, cap 1000 turns, seed 1:

| start / salary / rent | 2 players | 3 players | 4 players |
|---|---|---|---|
| 1500 / 200 / 50% (previous) | 3% finish, median 312 turns | 0% | 0% |
| 1000 / 50 / 100% (default) | 100%, median 27 turns | 95.7%, median 59 turns | 91%, median 121 turns |

## 3. Decisions on ambiguities

| #   | Question | Decision | Why |
|-----|----------|----------|-----|
| D1  | How many dice? | One six-sided die. | The statement says "a die". |
| D2  | Is buying optional? | No. Landing on an unowned property buys it automatically. | The statement says "he buys it"; it also removes a whole interaction from the timebox. |
| D3  | What if the player cannot afford the price? | Nothing is bought; the property stays unowned. Buying with exactly all your money is allowed. | Buying must never bankrupt anyone: only rent does (statement). |
| D4  | Salary on landing on Start, or only when passing? | Both: whenever the move crosses or ends on Start. No salary at game start. | The common reading of "passing Start"; it keeps the rule a single wrap-around check. |
| D5  | Order inside a turn | Roll, move, salary, then the effect of the landing square. | The salary earned on the way can help pay the rent at arrival. |
| D6  | Partial rent | If money < rent, the owner receives everything the player has left, and the player is eliminated. | Closest to real Monopoly without implementing liquidation. |
| D7  | Properties of a bankrupt player | They return to the bank and can be bought again. | Keeps the board alive with fewer players. |
| D8  | Turn order | Join order (creator first). Bankrupt players are skipped. | Simple and predictable. |
| D9  | When does the game start? | Automatically, as soon as every seat is taken. | The creator already chose the seat count; no extra "start" action needed. |
| D10 | Who rolls the die? | The server. | A client-side roll could be forged. |
| D11 | Player identity | Joining returns a secret player token; playing a turn requires it. | Prevents a player from playing for someone else. No accounts. |
| D12 | A player leaves mid-game | Out of scope: the game waits for them (they can reload the page and continue). | No turn timer or kick in the timebox. |
| D13 | Endless games | No turn limit; the default economy is tuned so games end. | Rent only moves money between players while the salary adds money every lap, so a high salary and low rents never end a game. With the defaults, simulated games finish within 1000 turns 100% of the time with 2 players (median 27 turns) and 91% with 4 players (median 121 turns); see the economy check above. |
| D14 | Can the economy be changed? | Yes: the creator may set starting money, salary and rent (as a percentage of the price) within the bounds above; absent settings take the defaults. The game state shows them. | Lets players trade a longer game for a shorter one without code changes; bounds keep games playable. |

Out of scope on purpose: doubles, jail, cards, houses, trading, mortgages, auctions.

## 4. Acceptance scenarios

### Domain rules
- **Move:** Given a game in progress, when the active player rolls N, then they move N squares, wrapping around the board.
- **Salary:** Given a player whose move crosses or ends on Start, then they receive the salary.
- **Buy:** Given an unowned property and enough money, when a player lands on it, then they pay the price and own it.
- **Cannot afford:** Given an unowned property priced above the player's money, when they land on it, then nothing changes.
- **Rent:** Given a property owned by another player, when a player lands on it, then the rent goes from the player to the owner.
- **Own property:** Given a property owned by the active player, when they land on it, then nothing happens.
- **Bankruptcy:** Given a player who cannot pay the full rent, then the owner receives what the player has left, the player is eliminated and their properties become unowned.
- **Winner:** Given only one player is left, then they win and the game is finished.
- **Turn order:** After a turn, the next non-bankrupt player becomes active.
- **Guards:** Only the active player can play, and only while the game is in progress.

### Lobby
- **Create:** Given a name and a seat count between 2 and 4, when creating a game, then the game is waiting for players and the creator holds the first seat.
- **Settings:** Given no settings, a new game uses the defaults; given valid settings, the game uses them and shows them in its state; settings out of bounds are rejected.
- **Join:** Given a waiting game, when a player joins, then they take the next seat; when the last seat is taken, the game starts.
- **Rejected join:** Joining an unknown, full or started game is rejected.
- **Authorization:** Playing a turn with a missing token or another player's token is rejected.

### Live updates
- **Broadcast:** Given players connected to a game, when it changes, then each of them receives the new state and the events that produced it.
- **Late join:** A client connecting to a game receives its current state right away.
