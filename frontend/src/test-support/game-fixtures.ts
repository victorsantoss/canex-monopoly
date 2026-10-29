import type { GameState, PlayerView, Square } from '../api/types'

function makeBoard(): Square[] {
  return Array.from({ length: 16 }, (_, index): Square => {
    if (index === 0) {
      return { index, kind: 'start', name: 'Start', price: null, rent: null, owner_id: null }
    }
    if (index % 4 === 0) {
      return { index, kind: 'empty', name: 'Empty lot', price: null, rent: null, owner_id: null }
    }
    return {
      index,
      kind: 'property',
      name: `Street ${index}`,
      price: 50 + index * 10,
      rent: 20 + index * 5,
      owner_id: null,
    }
  })
}

export function makePlayer(id: string, name: string, overrides: Partial<PlayerView> = {}): PlayerView {
  return { id, name, money: 1500, position: 0, is_bankrupt: false, ...overrides }
}

export function makeState(overrides: Partial<GameState> = {}): GameState {
  return {
    code: 'K7Q2XA',
    status: 'in_progress',
    seats: 2,
    current_player_id: 'p1',
    winner_id: null,
    board: makeBoard(),
    players: [makePlayer('p1', 'Ana'), makePlayer('p2', 'Bruno')],
    ...overrides,
  }
}
