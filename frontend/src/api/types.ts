// snake_case on purpose: mirroring the wire format leaves no mapping layer to drift from the server.

export type PlayerId = string

export type GameStatus = 'waiting' | 'in_progress' | 'finished'

export type SquareKind = 'start' | 'property' | 'empty'

export interface Square {
  index: number
  kind: SquareKind
  name: string
  price: number | null
  rent: number | null
  owner_id: PlayerId | null
}

export interface PlayerView {
  id: PlayerId
  name: string
  money: number
  position: number
  is_bankrupt: boolean
}

export interface GameSettings {
  starting_money: number
  salary: number
  rent_percent: number
}

export interface GameState {
  code: string
  status: GameStatus
  seats: number
  current_player_id: PlayerId | null
  winner_id: PlayerId | null
  settings: GameSettings
  board: Square[]
  players: PlayerView[]
}

export interface JoinedGame {
  code: string
  player_id: PlayerId
  player_token: string
}

export type GameEvent =
  | { type: 'player_joined'; player_id: PlayerId; player_name: string }
  | { type: 'game_started' }
  | { type: 'dice_rolled'; player_id: PlayerId; value: number }
  | { type: 'player_moved'; player_id: PlayerId; from_position: number; to_position: number }
  | { type: 'salary_received'; player_id: PlayerId; amount: number }
  | { type: 'property_bought'; player_id: PlayerId; square_index: number; price: number }
  | { type: 'property_unaffordable'; player_id: PlayerId; square_index: number }
  | {
      type: 'rent_paid'
      player_id: PlayerId
      owner_id: PlayerId
      square_index: number
      amount: number
    }
  | { type: 'player_bankrupted'; player_id: PlayerId; creditor_id: PlayerId }
  | { type: 'turn_passed'; player_id: PlayerId }
  | { type: 'game_won'; player_id: PlayerId }

export interface TurnPlayed {
  state: GameState
  events: GameEvent[]
}

export interface GameUpdatedMessage {
  type: 'game_updated'
  state: GameState
  events: GameEvent[]
}
