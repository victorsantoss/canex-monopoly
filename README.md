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

<!-- filled at the end of the timebox -->
