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
- More people than seats: once every seat is taken the game starts and any further join is
  rejected with `409`. Two people racing for the last seat cannot both get it: the join runs
  without any `await` between load and save (ADR 3), so one wins and the other gets `409`.
- Anyone with the code can still open the WebSocket and **watch** the game. Spectating is
  read-only by construction: playing requires a seat token, and the broadcast state has no tokens.
- `sessionStorage` dies with the tab. The seat is recovered with a private resume link
  (`/games/{code}#player=<id>&token=<token>`), which also lets a player continue on another device.
  The token travels in the URL fragment, so it never reaches server or proxy logs nor the `Referer`
  header, and the page strips it from the address bar at once. Preferred over `localStorage`, which
  only survives on the same browser and would make every tab of it the same player.
- Game codes are guessable by brute force (32^6 ≈ 10^9) and there is no rate limiting: acceptable
  for a demo, listed in the README as next work.
