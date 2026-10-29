import { makePlayer, makeState } from '../test-support/game-fixtures'
import { isMyTurn, playerColor } from './game-view'

describe('isMyTurn', () => {
  it('is true when the game is in progress and I am the current player', () => {
    expect(isMyTurn(makeState({ current_player_id: 'p1' }), 'p1')).toBe(true)
  })

  it('is false when another player is active', () => {
    expect(isMyTurn(makeState({ current_player_id: 'p2' }), 'p1')).toBe(false)
  })

  it.each(['waiting', 'finished'] as const)('is false while the game is %s', (status) => {
    expect(isMyTurn(makeState({ status, current_player_id: 'p1' }), 'p1')).toBe(false)
  })
})

describe('playerColor', () => {
  const players = [makePlayer('p1', 'Ana'), makePlayer('p2', 'Bruno'), makePlayer('p3', 'Carla')]

  it('gives each seat a distinct, stable color from its turn-order index', () => {
    const colors = players.map((player) => playerColor(players, player.id))

    expect(new Set(colors).size).toBe(3)
    expect(playerColor(players, 'p2')).toBe(colors[1])
  })

  it('returns a neutral color for an unknown player', () => {
    expect(playerColor(players, 'p9')).toBe('transparent')
  })
})
