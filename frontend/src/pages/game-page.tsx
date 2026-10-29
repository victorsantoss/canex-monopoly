import { useState } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import type { JoinedGame } from '../api/types'
import { GameScreen } from '../game/game-screen'
import { JoinGameForm } from '../lobby/join-game-form'
import {
  clearPlayerSession,
  loadPlayerSession,
  savePlayerSession,
  type PlayerSession,
} from '../session/player-session'
import { parseResumeFragment } from '../session/resume-link'

export function GamePage() {
  const { code } = useParams()
  if (code === undefined) return <Navigate to="/" replace />
  // Keyed by code so that following a link to another game loads that game's seat.
  return <GameForCode key={code} code={code.toUpperCase()} />
}

// Stripped from the address bar at once so the token neither lingers in history nor gets copied along.
function adoptSeatFromFragment(code: string): void {
  const seat = parseResumeFragment(window.location.hash)
  if (seat === null) return
  savePlayerSession(code, seat)
  window.history.replaceState(window.history.state, '', window.location.pathname + window.location.search)
}

function GameForCode({ code }: { code: string }) {
  const [session, setSession] = useState<PlayerSession | null>(() => {
    adoptSeatFromFragment(code)
    return loadPlayerSession(code)
  })

  const takeSeat = (joined: JoinedGame): void => {
    const newSession = { playerId: joined.player_id, playerToken: joined.player_token }
    savePlayerSession(joined.code, newSession)
    setSession(newSession)
  }

  const leaveSeat = (): void => {
    clearPlayerSession(code)
    setSession(null)
  }

  if (session === null) {
    return (
      <main>
        <JoinGameForm codeFromLink={code} onJoined={takeSeat} />
      </main>
    )
  }

  return <GameScreen code={code} session={session} onSeatRejected={leaveSeat} />
}
