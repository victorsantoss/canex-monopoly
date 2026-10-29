import { useState } from 'react'
import { ApiError, errorMessage, playTurn } from '../api/game-api'
import type { GameState } from '../api/types'
import type { PlayerSession } from '../session/player-session'
import { isMyTurn } from './game-view'

interface RollButtonProps {
  state: GameState
  session: PlayerSession
  onSeatRejected: () => void
}

export function RollButton({ state, session, onSeatRejected }: RollButtonProps) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const roll = async (): Promise<void> => {
    setPending(true)
    setError(null)
    try {
      // Response ignored on purpose: the game channel is the single source of updates, for this player too.
      await playTurn(state.code, session.playerToken)
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) {
        onSeatRejected()
        return
      }
      setError(errorMessage(reason))
    } finally {
      setPending(false)
    }
  }

  return (
    <div>
      <button type="button" onClick={roll} disabled={pending || !isMyTurn(state, session.playerId)}>
        Roll the die
      </button>
      {error !== null && <p role="alert">{error}</p>}
    </div>
  )
}
