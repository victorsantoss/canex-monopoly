# API contract

The contract shared by the backend and the frontend. All payloads are JSON, in `snake_case`.

## REST

Errors always have the shape `{ "detail": "<human readable message>" }`.

| Method | Path | Body | Success | Errors |
|--------|------|------|---------|--------|
| `POST` | `/api/games` | `{ "player_name": string, "seats": 2-4, "settings"?: GameSettingsInput }` | `201` `JoinedGame` | `422` invalid input |
| `POST` | `/api/games/{code}/players` | `{ "player_name": string }` | `201` `JoinedGame` | `404` unknown game, `409` game full or already started, `422` |
| `GET`  | `/api/games/{code}` | — | `200` `GameState` | `404` |
| `POST` | `/api/games/{code}/turns` | — (header `X-Player-Token`) | `200` `TurnPlayed` | `401` missing or unknown token, `403` not your turn, `404`, `409` game not in progress |

`player_name`: 1 to 20 characters after trimming.

`settings` and each of its fields are optional; a missing field takes its default. Out-of-bounds
values are rejected with `422`.

```jsonc
// GameSettingsInput
{
  "starting_money": 1000,  // 100 to 10000
  "salary": 50,            // 0 to 1000
  "rent_percent": 100      // 10 to 200: rent = price * rent_percent / 100, rounded down
}
```

```jsonc
// JoinedGame
{ "code": "K7Q2XA", "player_id": "p1", "player_token": "<secret>" }

// TurnPlayed
{ "state": GameState, "events": GameEvent[] }
```

## WebSocket

`/ws/games/{code}` — server to client only. Unknown game: the socket is closed with code `4404`.

On connection, and after every change of the game, each socket receives:

```jsonc
{ "type": "game_updated", "state": GameState, "events": GameEvent[] }
```

`events` is empty for the message sent on connection.

## Shapes

```jsonc
// GameState — never contains player tokens; `rent` follows the game's `rent_percent`
{
  "code": "K7Q2XA",
  "status": "waiting" | "in_progress" | "finished",
  "seats": 3,
  "current_player_id": "p2" | null,   // null unless in_progress
  "winner_id": "p1" | null,
  "settings": { "starting_money": 1000, "salary": 50, "rent_percent": 100 },
  "board": [
    { "index": 0, "kind": "start",    "name": "Start",        "price": null, "rent": null, "owner_id": null },
    { "index": 1, "kind": "property", "name": "Rue Ontario",  "price": 60,   "rent": 60,   "owner_id": "p1" },
    { "index": 2, "kind": "empty",    "name": "Empty lot",    "price": null, "rent": null, "owner_id": null }
  ],
  "players": [  // in turn order
    { "id": "p1", "name": "Ana", "money": 940, "position": 1, "is_bankrupt": false }
  ]
}
```

`GameEvent` is a union discriminated by `type`, listed in the order they happen within a turn:

| `type` | Fields |
|--------|--------|
| `player_joined` | `player_id`, `player_name` |
| `game_started` | — |
| `dice_rolled` | `player_id`, `value` |
| `player_moved` | `player_id`, `from_position`, `to_position` |
| `salary_received` | `player_id`, `amount` |
| `property_bought` | `player_id`, `square_index`, `price` |
| `property_unaffordable` | `player_id`, `square_index` |
| `rent_paid` | `player_id`, `owner_id`, `square_index`, `amount` |
| `player_bankrupted` | `player_id`, `creditor_id` |
| `turn_passed` | `player_id` (the new active player) |
| `game_won` | `player_id` |

Player ids are `p1`..`p4`, in join order. Game codes are 6 characters from `A-Z` and `2-9`
(no ambiguous `0/O`, `1/I`).
