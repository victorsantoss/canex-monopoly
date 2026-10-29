import type { GameState, PlayerId } from '../api/types'
import { playerColor } from './game-view'
import styles from './players-panel.module.scss'

interface PlayersPanelProps {
  state: GameState
  myPlayerId: PlayerId
}

export function PlayersPanel({ state, myPlayerId }: PlayersPanelProps) {
  return (
    <section aria-label="Players">
      <h2>Players</h2>
      <ul className={styles.players}>
        {state.players.map((player) => {
          const owned = state.board.filter((square) => square.owner_id === player.id)
          return (
            <li
              key={player.id}
              aria-label={`Player ${player.name}`}
              className={player.id === state.current_player_id ? `${styles.player} ${styles.active}` : styles.player}
              style={{ borderLeftColor: playerColor(state.players, player.id) }}
            >
              <div>
                <strong>{player.name}</strong> {player.id === myPlayerId && <span>(you)</span>}{' '}
                {player.id === state.current_player_id && <span>- playing</span>}
                {player.is_bankrupt && <span className={styles.bankrupt}>Bankrupt</span>}
              </div>
              <div>
                Money: <span>{player.money}</span>
              </div>
              {owned.length > 0 && (
                <ul className={styles.properties}>
                  {owned.map((square) => (
                    <li key={square.index}>{square.name}</li>
                  ))}
                </ul>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
