import { useState, type FormEvent } from 'react'
import { errorMessage, joinGame } from '../api/game-api'
import type { JoinedGame } from '../api/types'
import { loadPlayerSession } from '../session/player-session'

interface JoinGameFormProps {
  codeFromLink?: string
  onJoined: (joined: JoinedGame) => void
}

export function JoinGameForm({ codeFromLink, onJoined }: JoinGameFormProps) {
  const [typedCode, setTypedCode] = useState('')
  const [name, setName] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault()
    const code = codeFromLink ?? typedCode.trim().toUpperCase()
    // Joining again would take a second seat and overwrite the stored one, leaving the first
    // seat unplayable and the game stuck on its turn.
    const heldSeat = loadPlayerSession(code)
    if (heldSeat !== null) {
      onJoined({ code, player_id: heldSeat.playerId, player_token: heldSeat.playerToken })
      return
    }
    setPending(true)
    setError(null)
    try {
      onJoined(await joinGame(code, name.trim()))
    } catch (reason) {
      setError(errorMessage(reason))
      setPending(false)
    }
  }

  return (
    <form aria-label="Join a game" onSubmit={submit}>
      <h2>{codeFromLink === undefined ? 'Join a game' : `Join game ${codeFromLink}`}</h2>
      {codeFromLink === undefined && (
        <>
          <label htmlFor="join-code">Game code</label>
          <input id="join-code" value={typedCode} onChange={(e) => setTypedCode(e.target.value)} required />
        </>
      )}
      <label htmlFor="join-name">Your name</label>
      <input id="join-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={20} required />
      <button type="submit" disabled={pending}>
        Join game
      </button>
      {error !== null && <p role="alert">{error}</p>}
    </form>
  )
}
