import type { PlayerSession } from './player-session'

// Fragment, not query string: browsers never send it, so the token stays out of server logs and Referer.
export function buildResumeLink(code: string, session: PlayerSession): string {
  const fragment = new URLSearchParams({ player: session.playerId, token: session.playerToken })
  return `${location.origin}/games/${code}#${fragment.toString()}`
}

export function parseResumeFragment(fragment: string): PlayerSession | null {
  const params = new URLSearchParams(fragment.startsWith('#') ? fragment.slice(1) : fragment)
  const playerId = params.get('player')
  const playerToken = params.get('token')
  if (!playerId || !playerToken) return null
  return { playerId, playerToken }
}
