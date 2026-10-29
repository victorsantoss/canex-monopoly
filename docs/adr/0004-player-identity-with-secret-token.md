# 4. Player identity with a secret per-seat token

**Status:** accepted

## Context
There are no accounts, but a player must not be able to play someone else's turn.

## Decision
- Creating or joining a game returns a `player_id` (public) and a `player_token` (secret, random,
  generated with `secrets`).
- Playing a turn requires the token in the `X-Player-Token` header; the server maps it to the seat.
- The game state broadcast to everyone never contains tokens.
- The frontend keeps the token in `sessionStorage`, per game, so two tabs of the same browser can be
  two different players (handy for testing) and a reload keeps the seat.

## Consequences
- Anyone with the game code can join a free seat: the code is the invitation.
- Tokens are compared in constant time.
- No expiry or revocation; acceptable for a game that lives in memory.
