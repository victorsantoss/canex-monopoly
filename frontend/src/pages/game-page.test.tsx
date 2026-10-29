import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { joinGame } from '../api/game-api'
import { loadPlayerSession, savePlayerSession } from '../session/player-session'
import { FakeWebSocket } from '../test-support/fake-web-socket'
import { makePlayer, makeState } from '../test-support/game-fixtures'
import type { GameState } from '../api/types'
import { GamePage } from './game-page'

vi.mock('../api/game-api', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/game-api')>()
  return { ...original, joinGame: vi.fn(), playTurn: vi.fn() }
})

function renderGamePage(code = 'K7Q2XA') {
  render(
    <MemoryRouter initialEntries={[`/games/${code}`]}>
      <Routes>
        <Route path="/games/:code" element={<GamePage />} />
      </Routes>
    </MemoryRouter>,
  )
}

function pushState(state: GameState) {
  act(() => FakeWebSocket.latest().serverSend({ type: 'game_updated', state, events: [] }))
}

describe('GamePage', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.mocked(joinGame).mockReset()
    FakeWebSocket.instances = []
    vi.stubGlobal('WebSocket', FakeWebSocket)
  })

  afterEach(() => vi.unstubAllGlobals())

  it('offers to join this game when the visitor has no seat in it (shared link)', async () => {
    vi.mocked(joinGame).mockResolvedValue({ code: 'K7Q2XA', player_id: 'p2', player_token: 'secret-2' })
    renderGamePage()

    expect(screen.getByRole('heading', { name: 'Join game K7Q2XA' })).toBeInTheDocument()
    expect(FakeWebSocket.instances).toHaveLength(0)

    await userEvent.type(screen.getByLabelText('Your name'), 'Bruno')
    await userEvent.click(screen.getByRole('button', { name: 'Join game' }))

    expect(joinGame).toHaveBeenCalledWith('K7Q2XA', 'Bruno')
    expect(loadPlayerSession('K7Q2XA')).toEqual({ playerId: 'p2', playerToken: 'secret-2' })
    expect(FakeWebSocket.instances).toHaveLength(1)
  })

  it('shows the invite link and the seat count while waiting', () => {
    savePlayerSession('K7Q2XA', { playerId: 'p1', playerToken: 'secret' })
    renderGamePage()

    pushState(makeState({ status: 'waiting', seats: 3, current_player_id: null, players: [makePlayer('p1', 'Ana')] }))

    expect(screen.getByText('1/3 players joined')).toBeInTheDocument()
    expect(screen.getByDisplayValue(`${location.origin}/games/K7Q2XA`)).toBeInTheDocument()
  })

  it("shows the board, everyone's money and properties, and marks my seat", () => {
    savePlayerSession('K7Q2XA', { playerId: 'p2', playerToken: 'secret' })
    renderGamePage()
    const state = makeState({ players: [makePlayer('p1', 'Ana', { money: 1440 }), makePlayer('p2', 'Bruno')] })
    state.board[1] = { ...state.board[1], owner_id: 'p1' }

    pushState(state)

    expect(screen.getAllByRole('listitem', { name: /^Square/ })).toHaveLength(16)
    const ana = screen.getByRole('listitem', { name: 'Player Ana' })
    expect(within(ana).getByText('1440')).toBeInTheDocument()
    expect(within(ana).getByText('Street 1')).toBeInTheDocument()
    expect(within(screen.getByRole('listitem', { name: 'Player Bruno' })).getByText('(you)')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Roll the die' })).toBeDisabled()
  })

  it('announces the winner', () => {
    savePlayerSession('K7Q2XA', { playerId: 'p1', playerToken: 'secret' })
    renderGamePage()

    pushState(
      makeState({
        status: 'finished',
        current_player_id: null,
        winner_id: 'p1',
        players: [makePlayer('p1', 'Ana'), makePlayer('p2', 'Bruno', { is_bankrupt: true, money: 0 })],
      }),
    )

    expect(screen.getByRole('status')).toHaveTextContent('Ana wins!')
  })

  it('reports an unknown game', () => {
    savePlayerSession('ZZZZZZ', { playerId: 'p1', playerToken: 'secret' })
    renderGamePage('ZZZZZZ')

    act(() => FakeWebSocket.latest().serverClose(4404))

    expect(screen.getByText('This game does not exist.')).toBeInTheDocument()
  })
})
