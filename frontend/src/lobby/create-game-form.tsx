import { useState, type FormEvent } from 'react'
import { createGame, errorMessage } from '../api/game-api'
import type { JoinedGame } from '../api/types'

const SEAT_OPTIONS = [2, 3, 4]

interface CreateGameFormProps {
  onJoined: (joined: JoinedGame) => void
}

export function CreateGameForm({ onJoined }: CreateGameFormProps) {
  const [name, setName] = useState('')
  const [seats, setSeats] = useState(2)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault()
    setPending(true)
    setError(null)
    try {
      onJoined(await createGame(name.trim(), seats))
    } catch (reason) {
      setError(errorMessage(reason))
      setPending(false)
    }
  }

  return (
    <form aria-label="Create a game" onSubmit={submit}>
      <h2>Create a game</h2>
      <label htmlFor="create-name">Your name</label>
      <input id="create-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={20} required />
      <label htmlFor="create-seats">Players</label>
      <select id="create-seats" value={seats} onChange={(e) => setSeats(Number(e.target.value))}>
        {SEAT_OPTIONS.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
      <button type="submit" disabled={pending}>
        Create game
      </button>
      {error !== null && <p role="alert">{error}</p>}
    </form>
  )
}
