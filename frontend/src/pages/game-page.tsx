import { useState } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import type { JoinedGame } from '../api/types'
import { GameScreen } from '../game/game-screen'
import { JoinGameForm } from '../lobby/join-game-form'
import { loadPlayerSession, savePlayerSession, type PlayerSession } from '../session/player-session'

export function GamePage() {
  const { code } = useParams()
  if (code === undefined) return <Navigate to="/" replace />
  // Keyed by code so that following a link to another game reloads that game's seat.
  return <GameForCode key={code} code={code.toUpperCase()} />
}

function GameForCode({ code }: { code: string }) {
  const [session, setSession] = useState<PlayerSession | null>(() => loadPlayerSession(code))

  const takeSeat = (joined: JoinedGame): void => {
    const newSession = { playerId: joined.player_id, playerToken: joined.player_token }
    savePlayerSession(joined.code, newSession)
    setSession(newSession)
  }

  if (session === null) {
    return (
      <main>
        <JoinGameForm code={code} onJoined={takeSeat} />
      </main>
    )
  }

  return <GameScreen code={code} session={session} />
}
