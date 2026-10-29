import type { GameSettings, GameState, PlayerId, PlayerView } from '../api/types'
import type { LoggedEvent } from '../api/use-game-channel'

export function isMyTurn(state: GameState, playerId: PlayerId): boolean {
  return state.status === 'in_progress' && state.current_player_id === playerId
}

export function describeSettings(settings: GameSettings): string {
  return `Start ${settings.starting_money} · Salary ${settings.salary} · Rent ${settings.rent_percent}% of price`
}

// Dark enough for white initials on a token to meet WCAG AA contrast.
const SEAT_COLORS = ['#b8323f', '#00697a', '#8a5a00', '#5b3f86']

export function playerColor(players: PlayerView[], playerId: PlayerId | null): string {
  const seat = players.findIndex((player) => player.id === playerId)
  return seat === -1 ? 'transparent' : SEAT_COLORS[seat % SEAT_COLORS.length]
}

// Upper bound of each colour band; the board has no explicit street groups, so price stands in for them.
const PRICE_GROUP_CEILINGS = [80, 140, 180, 240, 300]

export function priceGroup(price: number): number {
  const group = PRICE_GROUP_CEILINGS.findIndex((ceiling) => price <= ceiling)
  return group === -1 ? PRICE_GROUP_CEILINGS.length : group
}

export function lastDiceRoll(entries: LoggedEvent[]): number | null {
  for (let index = entries.length - 1; index >= 0; index--) {
    const { event } = entries[index]
    if (event.type === 'dice_rolled') return event.value
  }
  return null
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
