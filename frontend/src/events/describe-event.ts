import type { GameEvent, GameState, PlayerId } from '../api/types'

export type EventContext = Pick<GameState, 'players' | 'board'>

export function describeEvent(event: GameEvent, context: EventContext): string {
  const player = (id: PlayerId): string =>
    context.players.find((candidate) => candidate.id === id)?.name ?? id
  const square = (index: number): string =>
    context.board.find((candidate) => candidate.index === index)?.name ?? `square ${index}`

  switch (event.type) {
    case 'player_joined':
      return `${event.player_name} joined the game`
    case 'game_started':
      return 'The game started'
    case 'dice_rolled':
      return `${player(event.player_id)} rolled a ${event.value}`
    case 'player_moved':
      return `${player(event.player_id)} moved to ${square(event.to_position)}`
    case 'salary_received':
      return `${player(event.player_id)} received a salary of ${event.amount}`
    case 'property_bought':
      return `${player(event.player_id)} bought ${square(event.square_index)} for ${event.price}`
    case 'property_unaffordable':
      return `${player(event.player_id)} cannot afford ${square(event.square_index)}`
    case 'rent_paid':
      return `${player(event.player_id)} paid ${event.amount} rent to ${player(event.owner_id)}`
    case 'player_bankrupted':
      return `${player(event.player_id)} went bankrupt`
    case 'turn_passed':
      return `It is ${player(event.player_id)}'s turn`
    case 'game_won':
      return `${player(event.player_id)} wins!`
  }
}
