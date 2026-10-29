import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom'
import { ApiError, createGame, joinGame } from '../api/game-api'
import { loadPlayerSession, savePlayerSession } from '../session/player-session'
import { LobbyPage } from './lobby-page'

vi.mock('../api/game-api', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/game-api')>()
  return { ...original, createGame: vi.fn(), joinGame: vi.fn() }
})

function GameRouteProbe() {
  const { code } = useParams()
  return <p>Game route {code}</p>
}

function renderLobby() {
  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<LobbyPage />} />
        <Route path="/games/:code" element={<GameRouteProbe />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('LobbyPage', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.mocked(createGame).mockReset()
    vi.mocked(joinGame).mockReset()
  })

  it('creates a game, keeps the seat and opens the game', async () => {
    vi.mocked(createGame).mockResolvedValue({ code: 'K7Q2XA', player_id: 'p1', player_token: 'secret' })
    renderLobby()

    await userEvent.type(screen.getByLabelText('Your name', { selector: '#create-name' }), 'Ana')
    await userEvent.selectOptions(screen.getByLabelText('Players'), '3')
    await userEvent.click(screen.getByRole('button', { name: 'Create game' }))

    expect(createGame).toHaveBeenCalledWith('Ana', 3, { starting_money: 1000, salary: 50, rent_percent: 100 })
    expect(await screen.findByText('Game route K7Q2XA')).toBeInTheDocument()
    expect(loadPlayerSession('K7Q2XA')).toEqual({ playerId: 'p1', playerToken: 'secret' })
  })

  it('offers the game settings pre-filled with the defaults and sends the chosen ones', async () => {
    vi.mocked(createGame).mockResolvedValue({ code: 'K7Q2XA', player_id: 'p1', player_token: 'secret' })
    renderLobby()

    expect(screen.getByLabelText('Starting money')).toHaveValue(1000)
    expect(screen.getByLabelText('Salary')).toHaveValue(50)
    expect(screen.getByLabelText('Rent (% of price)')).toHaveValue(100)

    await userEvent.type(screen.getByLabelText('Your name', { selector: '#create-name' }), 'Ana')
    await userEvent.clear(screen.getByLabelText('Starting money'))
    await userEvent.type(screen.getByLabelText('Starting money'), '2500')
    await userEvent.clear(screen.getByLabelText('Salary'))
    await userEvent.type(screen.getByLabelText('Salary'), '120')
    await userEvent.clear(screen.getByLabelText('Rent (% of price)'))
    await userEvent.type(screen.getByLabelText('Rent (% of price)'), '50')
    await userEvent.click(screen.getByRole('button', { name: 'Create game' }))

    expect(createGame).toHaveBeenCalledWith('Ana', 2, { starting_money: 2500, salary: 120, rent_percent: 50 })
  })

  it('joins a game by code', async () => {
    vi.mocked(joinGame).mockResolvedValue({ code: 'K7Q2XA', player_id: 'p2', player_token: 'secret-2' })
    renderLobby()

    await userEvent.type(screen.getByLabelText('Game code'), ' k7q2xa ')
    await userEvent.type(screen.getByLabelText('Your name', { selector: '#join-name' }), 'Bruno')
    await userEvent.click(screen.getByRole('button', { name: 'Join game' }))

    expect(joinGame).toHaveBeenCalledWith('K7Q2XA', 'Bruno')
    expect(await screen.findByText('Game route K7Q2XA')).toBeInTheDocument()
    expect(loadPlayerSession('K7Q2XA')).toEqual({ playerId: 'p2', playerToken: 'secret-2' })
  })

  it('reopens a game this tab already holds a seat in instead of joining it again', async () => {
    savePlayerSession('K7Q2XA', { playerId: 'p1', playerToken: 'first-seat' })
    renderLobby()

    await userEvent.type(screen.getByLabelText('Game code'), 'k7q2xa')
    await userEvent.type(screen.getByLabelText('Your name', { selector: '#join-name' }), 'Bruno')
    await userEvent.click(screen.getByRole('button', { name: 'Join game' }))

    expect(await screen.findByText('Game route K7Q2XA')).toBeInTheDocument()
    expect(joinGame).not.toHaveBeenCalled()
    expect(loadPlayerSession('K7Q2XA')).toEqual({ playerId: 'p1', playerToken: 'first-seat' })
  })

  it('shows why a join was rejected', async () => {
    vi.mocked(joinGame).mockRejectedValue(new ApiError(409, 'Game is full'))
    renderLobby()

    await userEvent.type(screen.getByLabelText('Game code'), 'K7Q2XA')
    await userEvent.type(screen.getByLabelText('Your name', { selector: '#join-name' }), 'Bruno')
    await userEvent.click(screen.getByRole('button', { name: 'Join game' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Game is full')
  })
})
