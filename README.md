# Monopoly — simplified, multiplayer

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
pip install -e ".[dev]"
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

## Quality checks

```bash
# backend/
pytest -q              # unit tests (next to the code) + acceptance tests (tests/acceptance)
ruff check . && ruff format --check .
mypy                   # strict

# frontend/
npm test
npm run typecheck
npm run lint
npm run build
```

## How the work was organised

Spec first, then acceptance tests, then unit tests per layer (ATDD + TDD):

1. [`docs/spec.md`](docs/spec.md) — rules, **decisions on every ambiguity (D1–D13)**, acceptance scenarios.
2. [`docs/api.md`](docs/api.md) — the REST + WebSocket contract, written before any code so the
   backend and the frontend could be built in parallel.
3. [`docs/adr/`](docs/adr) — architectural decisions.
4. One GitHub issue per vertical slice, one PR per issue; each PR maps acceptance criteria to tests.

## Architecture

```
backend/src/monopoly/
  domain/        pure game rules: Game aggregate, board, players, events, errors
  application/   use cases + ports (GameRepository, GameNotifier, Dice, ...)
  adapters/      FastAPI routes (driving), in-memory repository, random dice, WebSocket hub (driven)
  main.py        composition root
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

- One six-sided die; 16-square board; start with 1500; salary 200 when passing **or** landing on Start.
- Buying is automatic; if you cannot afford it, nothing happens (buying never bankrupts you).
- Cannot pay the full rent → the owner gets what you have left, you are eliminated, your
  properties return to the bank.
- The game starts as soon as all seats are taken; turn order is join order.

## With more time

- **Game browser** (waiting / in progress / finished): a `list(status)` query on the
  `GameRepository` port, a `list_games` use case and a REST adapter. It needs a public/private
  `visibility` on the game first: listing waiting games would expose their codes, which are the
  invitation today.
- **Persistence and scale-out** ([ADR 3](docs/adr/0003-in-memory-single-process.md)): a
  PostgreSQL adapter for `GameRepository` with optimistic concurrency (a version per game), and a
  Redis pub/sub adapter for `GameNotifier`, so games survive restarts and several instances can
  serve the same game. The domain does not change.
- **Seat recovery after closing the tab:** this is a client-side loss (the token lived in
  `sessionStorage`), so a database alone does not fix it. Options: `localStorage` keyed by game, a
  private "resume" link carrying the token, or accounts.
- **Abuse protection:** rate limiting on joins (codes are brute-forceable), game expiry.
- **Optional accounts** to reconnect from another device (today a closed tab loses its seat).
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
