import { ApiError, createGame, getGame, joinGame, playTurn } from './game-api'
import type { GameState, JoinedGame } from './types'

const joined: JoinedGame = { code: 'K7Q2XA', player_id: 'p1', player_token: 'secret' }

const state: GameState = {
  code: 'K7Q2XA',
  status: 'waiting',
  seats: 2,
  current_player_id: null,
  winner_id: null,
  settings: { starting_money: 1000, salary: 50, rent_percent: 100 },
  board: [],
  players: [],
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('game api', () => {
  const fetchMock = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('creates a game with its settings', async () => {
    fetchMock.mockResolvedValue(jsonResponse(201, joined))
    const settings = { starting_money: 2500, salary: 120, rent_percent: 50 }

    await expect(createGame('Ana', 3, settings)).resolves.toEqual(joined)

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/games')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(String(init?.body))).toEqual({ player_name: 'Ana', seats: 3, settings })
  })

  it('joins a game, encoding the code in the path', async () => {
    fetchMock.mockResolvedValue(jsonResponse(201, joined))

    await joinGame('K7Q2XA', 'Bruno')

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/games/K7Q2XA/players')
    expect(JSON.parse(String(init?.body))).toEqual({ player_name: 'Bruno' })
  })

  it('gets a game', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, state))

    await expect(getGame('K7Q2XA')).resolves.toEqual(state)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/games/K7Q2XA')
  })

  it('plays a turn with the player token header', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { state, events: [] }))

    await expect(playTurn('K7Q2XA', 'secret')).resolves.toEqual({ state, events: [] })

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/games/K7Q2XA/turns')
    expect(init?.method).toBe('POST')
    expect(new Headers(init?.headers).get('X-Player-Token')).toBe('secret')
  })

  it('throws an ApiError with the status and the server detail', async () => {
    fetchMock.mockResolvedValue(jsonResponse(403, { detail: 'Not your turn' }))

    const error = await playTurn('K7Q2XA', 'secret').catch((reason: unknown) => reason)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 403, detail: 'Not your turn', message: 'Not your turn' })
  })

  it('uses a generic detail when the error body is not the documented shape', async () => {
    fetchMock.mockResolvedValue(new Response('Bad gateway', { status: 502 }))

    await expect(getGame('K7Q2XA')).rejects.toMatchObject({
      status: 502,
      detail: 'Request failed with status 502',
    })
  })
})
