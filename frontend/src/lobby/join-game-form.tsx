import { useState, type FormEvent } from 'react'
import { errorMessage, joinGame } from '../api/game-api'
import type { JoinedGame } from '../api/types'

interface JoinGameFormProps {
  // When the code comes from a shared link, the visitor only types a name.
  code?: string
  onJoined: (joined: JoinedGame) => void
}

export function JoinGameForm({ code, onJoined }: JoinGameFormProps) {
  const [typedCode, setTypedCode] = useState('')
  const [name, setName] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault()
    setPending(true)
    setError(null)
    try {
      onJoined(await joinGame(code ?? typedCode.trim().toUpperCase(), name.trim()))
    } catch (reason) {
      setError(errorMessage(reason))
      setPending(false)
    }
  }

  return (
    <form aria-label="Join a game" onSubmit={submit}>
      <h2>{code === undefined ? 'Join a game' : `Join game ${code}`}</h2>
      {code === undefined && (
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
