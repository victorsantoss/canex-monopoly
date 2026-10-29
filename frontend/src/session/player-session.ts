import type { PlayerId } from '../api/types'

export interface PlayerSession {
  playerId: PlayerId
  playerToken: string
}

// sessionStorage (not localStorage): two tabs of the same browser can hold two different seats,
// and a reload keeps the seat.
const keyFor = (code: string): string => `monopoly.session.${code}`

function isPlayerSession(value: unknown): value is PlayerSession {
  if (typeof value !== 'object' || value === null) return false
  const candidate = value as Record<string, unknown>
  return typeof candidate.playerId === 'string' && typeof candidate.playerToken === 'string'
}

export function savePlayerSession(code: string, session: PlayerSession): void {
  try {
    sessionStorage.setItem(keyFor(code), JSON.stringify(session))
  } catch {
    // Storage can be blocked (privacy mode); the seat then only lives until the page is closed.
  }
}

export function clearPlayerSession(code: string): void {
  try {
    sessionStorage.removeItem(keyFor(code))
  } catch {
    // Nothing was stored if storage is blocked.
  }
}

export function loadPlayerSession(code: string): PlayerSession | null {
  try {
    const raw = sessionStorage.getItem(keyFor(code))
    if (raw === null) return null
    const parsed: unknown = JSON.parse(raw)
    return isPlayerSession(parsed) ? parsed : null
  } catch {
    return null
  }
}
