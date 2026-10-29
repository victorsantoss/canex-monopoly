import type { GameEvent } from '../api/types'
import { describeEvent, type EventContext } from './describe-event'

const context: EventContext = {
  players: [
    { id: 'p1', name: 'Ana', money: 1500, position: 0, is_bankrupt: false },
    { id: 'p2', name: 'Bruno', money: 1500, position: 0, is_bankrupt: false },
  ],
  board: [
    { index: 0, kind: 'start', name: 'Start', price: null, rent: null, owner_id: null },
    { index: 1, kind: 'property', name: 'Rue Ontario', price: 60, rent: 30, owner_id: null },
  ],
}

describe('describeEvent', () => {
  it.each<[GameEvent, string]>([
    [{ type: 'player_joined', player_id: 'p2', player_name: 'Bruno' }, 'Bruno joined the game'],
    [{ type: 'game_started' }, 'The game started'],
    [{ type: 'dice_rolled', player_id: 'p1', value: 4 }, 'Ana rolled a 4'],
    [
      { type: 'player_moved', player_id: 'p1', from_position: 0, to_position: 1 },
      'Ana moved to Rue Ontario',
    ],
    [{ type: 'salary_received', player_id: 'p1', amount: 200 }, 'Ana received a salary of 200'],
    [
      { type: 'property_bought', player_id: 'p1', square_index: 1, price: 60 },
      'Ana bought Rue Ontario for 60',
    ],
    [
      { type: 'property_unaffordable', player_id: 'p1', square_index: 1 },
      'Ana cannot afford Rue Ontario',
    ],
    [
      { type: 'rent_paid', player_id: 'p2', owner_id: 'p1', square_index: 1, amount: 30 },
      'Bruno paid 30 rent to Ana',
    ],
    [{ type: 'player_bankrupted', player_id: 'p2', creditor_id: 'p1' }, 'Bruno went bankrupt'],
    [{ type: 'turn_passed', player_id: 'p2' }, "It is Bruno's turn"],
    [{ type: 'game_won', player_id: 'p1' }, 'Ana wins!'],
  ])('describes %o', (event, expected) => {
    expect(describeEvent(event, context)).toBe(expected)
  })

  it('falls back to the raw ids when a player or square is unknown', () => {
    expect(
      describeEvent({ type: 'property_bought', player_id: 'p9', square_index: 42, price: 10 }, context),
    ).toBe('p9 bought square 42 for 10')
  })
})
