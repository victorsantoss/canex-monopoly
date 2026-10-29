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
  // Kept as text so a field can be cleared while typing; the server validates the bounds.
  const [startingMoney, setStartingMoney] = useState('1000')
  const [salary, setSalary] = useState('50')
  const [rentPercent, setRentPercent] = useState('100')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault()
    setPending(true)
    setError(null)
    try {
      const settings = {
        starting_money: Number(startingMoney),
        salary: Number(salary),
        rent_percent: Number(rentPercent),
      }
      onJoined(await createGame(name.trim(), seats, settings))
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
      <fieldset>
        <legend>Game settings</legend>
        <label htmlFor="create-starting-money">Starting money</label>
        <input
          id="create-starting-money"
          type="number"
          min={100}
          max={10000}
          value={startingMoney}
          onChange={(e) => setStartingMoney(e.target.value)}
          required
        />
        <label htmlFor="create-salary">Salary</label>
        <input
          id="create-salary"
          type="number"
          min={0}
          max={1000}
          value={salary}
          onChange={(e) => setSalary(e.target.value)}
          required
        />
        <label htmlFor="create-rent-percent">Rent (% of price)</label>
        <input
          id="create-rent-percent"
          type="number"
          min={10}
          max={200}
          value={rentPercent}
          onChange={(e) => setRentPercent(e.target.value)}
          required
        />
      </fieldset>
      <button type="submit" disabled={pending}>
        Create game
      </button>
      {error !== null && <p role="alert">{error}</p>}
    </form>
  )
}
