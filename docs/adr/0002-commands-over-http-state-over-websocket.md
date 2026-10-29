# 2. Commands over HTTP, state pushed over WebSocket

**Status:** accepted

## Context
Players act (create, join, play) and everyone must see the result live.

## Decision
- Commands go through REST endpoints. They return an explicit status (`404`, `409`, `403`) that
  the client can handle, and they are trivial to test.
- After every successful command, the server pushes the **full game state** plus the **events**
  produced by that command to every WebSocket connected to the game.
- A client connecting to the WebSocket immediately receives the current state.

## Alternatives considered
- *Everything over WebSocket:* one channel, but request/response and error handling must be
  rebuilt by hand.
- *Polling:* simplest, but not "live", and wasteful.
- *Sending diffs instead of the full state:* smaller messages, but the client must apply them in
  order. The state of a game is a few hundred bytes, so a full snapshot is the simpler contract;
  the events are only there to tell the story (log, animations).

## Consequences
- Clients never compute the game state: they render what the server sends, so they cannot drift.
- If a push is lost, the next one repairs the client.
