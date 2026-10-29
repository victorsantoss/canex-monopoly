import type { PlayerSession } from './player-session'

// The seat travels in the fragment, never in the query string: browsers do not send fragments to the
// server, so the token stays out of access/proxy logs and out of the Referer header.
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
