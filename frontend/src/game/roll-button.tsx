import { useState } from 'react'
import { errorMessage, playTurn } from '../api/game-api'
import type { GameState } from '../api/types'
import type { PlayerSession } from '../session/player-session'
import { isMyTurn } from './game-view'

interface RollButtonProps {
  state: GameState
  session: PlayerSession
}

export function RollButton({ state, session }: RollButtonProps) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const roll = async (): Promise<void> => {
    setPending(true)
    setError(null)
    try {
      // The response is ignored on purpose: the same state and events reach every player,
      // this one included, through the game channel, so there is a single source of updates.
      await playTurn(state.code, session.playerToken)
    } catch (reason) {
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
