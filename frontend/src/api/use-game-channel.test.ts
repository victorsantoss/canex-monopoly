import { act, renderHook } from '@testing-library/react'
import { FakeWebSocket } from '../test-support/fake-web-socket'
import { makeState } from '../test-support/game-fixtures'
import { useGameChannel } from './use-game-channel'

describe('useGameChannel', () => {
  beforeEach(() => {
    FakeWebSocket.instances = []
    vi.stubGlobal('WebSocket', FakeWebSocket)
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('connects to the game channel on the current host', () => {
    const { result } = renderHook(() => useGameChannel('K7Q2XA'))

    expect(FakeWebSocket.latest().url).toBe(`ws://${location.host}/ws/games/K7Q2XA`)
    expect(result.current.connectionStatus).toBe('connecting')

    act(() => FakeWebSocket.latest().serverOpen())

    expect(result.current.connectionStatus).toBe('open')
  })

  it('renders the latest state and accumulates the events in order', () => {
    const { result } = renderHook(() => useGameChannel('K7Q2XA'))
    const socket = FakeWebSocket.latest()
    const initial = makeState({ status: 'waiting', current_player_id: null })
    const started = makeState()

    act(() => socket.serverSend({ type: 'game_updated', state: initial, events: [] }))
    expect(result.current.state).toEqual(initial)
    expect(result.current.eventLog).toEqual([])

    act(() =>
      socket.serverSend({
        type: 'game_updated',
        state: started,
        events: [{ type: 'player_joined', player_id: 'p2', player_name: 'Bruno' }, { type: 'game_started' }],
      }),
    )
    act(() =>
      socket.serverSend({
        type: 'game_updated',
        state: started,
        events: [{ type: 'dice_rolled', player_id: 'p1', value: 3 }],
      }),
    )

    expect(result.current.state).toEqual(started)
    expect(result.current.eventLog.map((entry) => entry.event.type)).toEqual([
      'player_joined',
      'game_started',
      'dice_rolled',
    ])
    expect(new Set(result.current.eventLog.map((entry) => entry.id)).size).toBe(3)
  })

  it('ignores messages it does not understand', () => {
    const { result } = renderHook(() => useGameChannel('K7Q2XA'))

    act(() => FakeWebSocket.latest().serverSendRaw('not json'))
    act(() => FakeWebSocket.latest().serverSend({ type: 'something_else' }))

    expect(result.current.state).toBeNull()
  })

  it('reconnects after an unexpected close', () => {
    const { result } = renderHook(() => useGameChannel('K7Q2XA', { reconnectDelayMs: 1000 }))

    act(() => FakeWebSocket.latest().serverClose(1006))
    expect(result.current.connectionStatus).toBe('reconnecting')
    expect(FakeWebSocket.instances).toHaveLength(1)

    act(() => vi.advanceTimersByTime(1000))

    expect(FakeWebSocket.instances).toHaveLength(2)
    expect(result.current.connectionStatus).toBe('connecting')
  })

  it('reports an unknown game and does not reconnect', () => {
    const { result } = renderHook(() => useGameChannel('ZZZZZZ', { reconnectDelayMs: 1000 }))

    act(() => FakeWebSocket.latest().serverClose(4404))
    act(() => vi.advanceTimersByTime(5000))

    expect(result.current.notFound).toBe(true)
    expect(FakeWebSocket.instances).toHaveLength(1)
  })

  it('closes the socket on unmount and does not reconnect', () => {
    const { unmount } = renderHook(() => useGameChannel('K7Q2XA', { reconnectDelayMs: 1000 }))
    const socket = FakeWebSocket.latest()

    unmount()
    socket.serverClose(1000)
    vi.advanceTimersByTime(5000)

    expect(socket.closedByClient).toBe(true)
    expect(FakeWebSocket.instances).toHaveLength(1)
  })
})
