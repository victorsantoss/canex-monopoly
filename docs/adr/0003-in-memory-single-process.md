# 3. In-memory persistence, single process

**Status:** accepted (timebox)

## Context
The exercise is time-boxed to two hours and does not require games to survive a restart.

## Decision
- Games live in an in-memory repository behind the `GameRepository` port.
- WebSocket connections are tracked in memory per game.
- Use cases are `async` and do not `await` between loading and saving a game, so on a single
  asyncio event loop two commands on the same game cannot interleave. No lock is needed.

## Consequences
- Restarting the server loses every game.
- The app cannot run with several workers or instances: a second process would not see the games
  nor the sockets of the first one.
- Scaling out means a shared store (e.g. PostgreSQL or Redis) with optimistic concurrency (a version
  on the game) and a pub/sub (e.g. Redis) for the notifier. Both are new adapters; the domain does
  not change.
