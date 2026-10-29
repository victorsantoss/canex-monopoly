import type { GameSettings, GameState, PlayerId, PlayerView } from '../api/types'

export function isMyTurn(state: GameState, playerId: PlayerId): boolean {
  return state.status === 'in_progress' && state.current_player_id === playerId
}

export function describeSettings(settings: GameSettings): string {
  return `Start ${settings.starting_money} · Salary ${settings.salary} · Rent ${settings.rent_percent}% of price`
}

const SEAT_COLORS = ['#d1495b', '#00798c', '#edae49', '#6a4c93']

export function playerColor(players: PlayerView[], playerId: PlayerId | null): string {
  const seat = players.findIndex((player) => player.id === playerId)
  return seat === -1 ? 'transparent' : SEAT_COLORS[seat % SEAT_COLORS.length]
}

export interface GridCell {
  row: number
  column: number
}

export function ringSide(boardSize: number): number {
  return boardSize / 4 + 1
}

// Clockwise around the edge of a square grid, Start in the top-left corner.
export function ringCell(index: number, boardSize: number): GridCell {
  const last = ringSide(boardSize)
  const side = last - 1
  if (index <= side) return { row: 1, column: index + 1 }
  if (index <= 2 * side) return { row: index - side + 1, column: last }
  if (index <= 3 * side) return { row: last, column: last - (index - 2 * side) }
  return { row: last - (index - 3 * side), column: 1 }
}
