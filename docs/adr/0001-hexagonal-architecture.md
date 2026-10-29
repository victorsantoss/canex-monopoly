# 1. Hexagonal architecture (ports and adapters) on the backend

**Status:** accepted

## Context
The game rules are the heart of the exercise and the part most likely to evolve during the
debrief. They must be testable without HTTP, WebSockets or a database.

## Decision
- `domain/` holds the rules as plain Python: the `Game` aggregate, the board, players and domain
  events. It imports nothing from FastAPI or the application layer.
- `application/` holds the use cases (`create_game`, `join_game`, `play_turn`) and the ports they
  depend on: `GameRepository`, `GameNotifier`, `Dice`, `CodeGenerator`, `TokenGenerator`.
- `adapters/` implement those ports (in-memory repository, random dice, WebSocket notifier) and the
  driving side (FastAPI routes).
- `main.py` is the composition root: the only place that wires adapters into use cases.

## Consequences
- Domain and use-case tests run in milliseconds with fakes (fixed dice, in-memory repository).
- A real database or a message broker becomes a new adapter, with no change to the rules.
- More files than a single-module FastAPI app; acceptable for the evaluation criteria.
