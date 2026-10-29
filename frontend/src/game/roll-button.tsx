import { useState } from 'react'
import { ApiError, errorMessage, playTurn } from '../api/game-api'
import type { GameState, PlayerId } from '../api/types'
import type { ConnectionStatus } from '../api/use-game-channel'
import type { PlayerSession } from '../session/player-session'
import { isMyTurn } from './game-view'

interface RollButtonProps {
  state: GameState
  session: PlayerSession
  connectionStatus: ConnectionStatus
  onSeatRejected: () => void
}

export function RollButton({ state, session, connectionStatus, onSeatRejected }: RollButtonProps) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorTurn, setErrorTurn] = useState<PlayerId | null>(state.current_player_id)

  // An error belongs to the turn it happened on; once the turn moves on it is stale.
  if (errorTurn !== state.current_player_id) {
    setErrorTurn(state.current_player_id)
    setError(null)
  }

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

  // While the channel is down, the state on screen may already be outdated.
  const canRoll = !pending && connectionStatus === 'open' && isMyTurn(state, session.playerId)

  return (
    <div>
      <button type="button" onClick={roll} disabled={!canRoll}>
        Roll the die
      </button>
      {error !== null && <p role="alert">{error}</p>}
    </div>
  )
}
