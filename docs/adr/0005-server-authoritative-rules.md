# 5. The server is authoritative; the client only renders

**Status:** accepted

## Context
Rules could be duplicated on the client for snappier feedback.

## Decision
The client never applies rules. It sends intents ("play my turn") and renders the state and events
it receives. The die is rolled on the server (spec D10).

## Consequences
- No rule duplication between Python and TypeScript, no cheating by forging a roll.
- Each action costs a round trip; irrelevant for a turn-based game.
