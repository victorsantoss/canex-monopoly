# Monopoly — simplified, multiplayer

[![CI](https://github.com/victorsantoss/canex-monopoly/actions/workflows/ci.yml/badge.svg)](https://github.com/victorsantoss/canex-monopoly/actions/workflows/ci.yml)

A simplified Monopoly played by 2 to 4 players, each from their own browser, with live updates.
Backend in Python + FastAPI, frontend in React + TypeScript (+ Sass).

> Take-home exercise, time-boxed to two hours. This README states what was built, the decisions
> taken, and what I would do next.

## Run it

Prerequisites: Python 3.11+, Node.js 20+ (LTS recommended).

**Backend** (http://localhost:8000):

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.lock   # pinned runtime + dev dependencies
pip install -e . --no-deps
uvicorn monopoly.main:app --reload --port 8000
```

**Frontend** (http://localhost:5173, proxies `/api` and `/ws` to the backend):

```bash
cd frontend
npm ci
npm run dev
```

The frontend and the API must share an origin: in development the Vite proxy does it; a
production build (`npm run build`) has to be served behind a reverse proxy that routes `/api` and
`/ws` to the backend.

**Play:** open http://localhost:5173, create a game, then open the invite link in other browsers
(or other tabs: each tab is a separate player, see [ADR 4](docs/adr/0004-player-identity-with-secret-token.md)).
A closed tab or another device takes the seat back through the **private link** shown on the game
screen (the token travels in the URL fragment, never sent to the server).

## Quality checks

```bash
# backend/
pytest -q              # unit tests (next to the code) + acceptance tests (tests/acceptance)
ruff check . scripts && ruff format --check .
mypy                   # strict

# frontend/
npm test
npm run typecheck
npm run lint
npm run build
```

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs the same gate on every pull
request and every push to `main`.

Backend dependencies are pinned in `backend/requirements.lock` (runtime) and
`backend/requirements-dev.lock` (runtime + dev), compiled from `pyproject.toml` with pip-tools.
After changing `pyproject.toml`, refresh both from `backend/` with
`pip-compile --strip-extras -o requirements.lock pyproject.toml && pip-compile --strip-extras --extra dev -o requirements-dev.lock pyproject.toml`.

## How the work was organised

Spec first, then acceptance tests, then unit tests per layer (ATDD + TDD):

1. [`docs/spec.md`](docs/spec.md) — rules, **decisions on every ambiguity (D1–D14)**, acceptance scenarios.
2. [`docs/api.md`](docs/api.md) — the REST + WebSocket contract, written before any code so the
   backend and the frontend could be built in parallel.
3. [`docs/adr/`](docs/adr) — architectural decisions.
4. One GitHub issue per vertical slice, one PR per issue; each PR maps acceptance criteria to tests.
   Independent slices (domain, WebSocket hub, frontend) were built in parallel against the contract.
5. A clean-code pass, then an independent review of the whole codebase; its findings were fixed in
   two PRs (aggregate encapsulation, error contract, WebSocket back-pressure, rejoin, token exposure).
6. Full games played in the browser and through the simulation script before calling it done.

## Architecture

```
backend/src/monopoly/
  domain/        pure game rules: Game aggregate, board, rules (economy), players, events, errors
  application/   use cases + ports (GameRepository, GameNotifier, Dice, ...)
  adapters/      FastAPI routes (driving), in-memory repository, random dice, WebSocket hub (driven)
  main.py        composition root
backend/scripts/ simulate_games.py: plays thousands of games to check the economy
frontend/src/
  api/           contract types, HTTP client, WebSocket hook
  session/       per-tab player token
  events/        event -> human sentence
  pages/, components/
```

- **Hexagonal backend** ([ADR 1](docs/adr/0001-hexagonal-architecture.md)): the rules have no
  framework dependency and are tested in isolation; adapters are replaceable.
- **Commands over HTTP, state pushed over WebSocket** ([ADR 2](docs/adr/0002-commands-over-http-state-over-websocket.md)):
  every change broadcasts the full game state plus the events that produced it.
- **Server-authoritative** ([ADR 5](docs/adr/0005-server-authoritative-rules.md)): the server rolls
  the die and applies the rules; the client only renders.
- **In-memory, single process** ([ADR 3](docs/adr/0003-in-memory-single-process.md)): a deliberate
  timebox shortcut, isolated behind ports.
- **Per-seat secret token** ([ADR 4](docs/adr/0004-player-identity-with-secret-token.md)): nobody can
  play someone else's turn.

## Rule interpretations (summary)

See [spec §3](docs/spec.md#3-decisions-on-ambiguities) for the full list and rationale.

- One six-sided die; 16-square board; salary when passing **or** landing on Start.
- Economy defaults: start with 1000, salary 50, rent equal to the price. The creator can change
  all three (within bounds) when creating a game.
- Buying is automatic; if you cannot afford it, nothing happens (buying never bankrupts you).
- Cannot pay the full rent → the owner gets what you have left, you are eliminated, your
  properties return to the bank.
- The game starts as soon as all seats are taken; turn order is join order.

## What playing it taught me

The first economy (start 1500, salary 200, rent 50% of the price) passed every rule test, yet a
full game never ended: rent only moves money between players while the salary keeps creating it.
Playing whole games through the domain showed it (`backend/scripts/simulate_games.py`):

| start / salary / rent | 2 players | 3 players | 4 players |
|---|---|---|---|
| 1500 / 200 / 50% (first version) | 3% finish within 1000 turns | 0% | 0% |
| 1000 / 50 / 100% (current default) | 100%, median 27 turns | 96%, median 59 | 91%, median 121 |

Unit tests check each rule; only a simulation checks that the rules together make a game.

## With more time

- **Game browser** (waiting / in progress / finished): a `list(status)` query on the
  `GameRepository` port, a `list_games` use case and a REST adapter. It needs a public/private
  `visibility` on the game first: listing waiting games would expose their codes, which are the
  invitation today.
- **Persistence and scale-out** ([ADR 3](docs/adr/0003-in-memory-single-process.md)): a
  PostgreSQL adapter for `GameRepository` with optimistic concurrency (a version per game), and a
  Redis pub/sub adapter for `GameNotifier`, so games survive restarts and several instances can
  serve the same game. The domain does not change.
- **Abuse protection:** rate limiting on joins (codes are brute-forceable), game expiry.
- **Optional accounts**, so a seat survives without keeping the private resume link.
- **Official rules kept out of scope on purpose** (the statement does not evaluate them), with
  the extension already designed:
  - *Jail* ([#16](https://github.com/victorsantoss/canex-monopoly/issues/16)): new square types in
    the `Square` union, one branch in `Game._resolve_square`, a `turns_in_jail` counter on the player.
  - *Houses and hotels* ([#17](https://github.com/victorsantoss/canex-monopoly/issues/17)): turns
    stop being fully automatic: a `TurnPhase` and new `build` / `end_turn` commands on the
    aggregate, a rent table per development level.
- **A round limit** (richest player wins) as an opt-in setting, for the few long 4-player games.
  Not done by default: it changes the win condition of the statement.
- **End-to-end browser tests** (Playwright) for the create, join, play and win flow; today it is
  covered by HTTP/WebSocket acceptance tests plus a manual run.
