import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ApiError, playTurn } from '../api/game-api'
import type { TurnPlayed } from '../api/types'
import { makeState } from '../test-support/game-fixtures'
import { RollButton } from './roll-button'

vi.mock('../api/game-api', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/game-api')>()
  return { ...original, playTurn: vi.fn() }
})

const playTurnMock = vi.mocked(playTurn)
const session = { playerId: 'p1', playerToken: 'secret' }

describe('RollButton', () => {
  beforeEach(() => playTurnMock.mockReset())

  it('is enabled on my turn', () => {
    render(<RollButton state={makeState({ current_player_id: 'p1' })} session={session} />)

    expect(screen.getByRole('button', { name: 'Roll the die' })).toBeEnabled()
  })

  it("is disabled on someone else's turn", () => {
    render(<RollButton state={makeState({ current_player_id: 'p2' })} session={session} />)

    expect(screen.getByRole('button', { name: 'Roll the die' })).toBeDisabled()
  })

  it('is disabled while the game is waiting for players', () => {
    render(<RollButton state={makeState({ status: 'waiting', current_player_id: null })} session={session} />)

    expect(screen.getByRole('button', { name: 'Roll the die' })).toBeDisabled()
  })

  it('plays the turn with my token and stays disabled while the request is pending', async () => {
    let resolve: (value: TurnPlayed) => void = () => {}
    playTurnMock.mockReturnValue(new Promise((done) => (resolve = done)))
    const state = makeState({ current_player_id: 'p1' })
    render(<RollButton state={state} session={session} />)
    const button = screen.getByRole('button', { name: 'Roll the die' })

    await userEvent.click(button)

    expect(playTurnMock).toHaveBeenCalledWith('K7Q2XA', 'secret')
    expect(button).toBeDisabled()

    resolve({ state, events: [] })
    await vi.waitFor(() => expect(button).toBeEnabled())
  })

  it('shows the server error', async () => {
    playTurnMock.mockRejectedValue(new ApiError(403, 'Not your turn'))
    render(<RollButton state={makeState({ current_player_id: 'p1' })} session={session} />)

    await userEvent.click(screen.getByRole('button', { name: 'Roll the die' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Not your turn')
  })
})
