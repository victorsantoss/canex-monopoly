import type { GameSettings, JoinedGame, TurnPlayed } from './types'

export class ApiError extends Error {
  readonly status: number
  readonly detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.detail : 'Could not reach the server. Please try again.'
}

async function readDetail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json()
    if (typeof body === 'object' && body !== null && 'detail' in body && typeof body.detail === 'string') {
      return body.detail
    }
  } catch {
    // Not JSON (e.g. a proxy error page): fall through to the generic message.
  }
  return `Request failed with status ${response.status}`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)
  if (!response.ok) {
    throw new ApiError(response.status, await readDetail(response))
  }
  return (await response.json()) as T
}

const gamePath = (code: string): string => `/api/games/${encodeURIComponent(code)}`

function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function createGame(playerName: string, seats: number, settings: GameSettings): Promise<JoinedGame> {
  return postJson<JoinedGame>('/api/games', { player_name: playerName, seats, settings })
}

export function joinGame(code: string, playerName: string): Promise<JoinedGame> {
  return postJson<JoinedGame>(`${gamePath(code)}/players`, { player_name: playerName })
}

export function playTurn(code: string, playerToken: string): Promise<TurnPlayed> {
  return request<TurnPlayed>(`${gamePath(code)}/turns`, {
    method: 'POST',
    headers: { 'X-Player-Token': playerToken },
  })
}
