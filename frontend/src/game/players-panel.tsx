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
          const color = playerColor(state.players, player.id)
          const stateClass = player.is_bankrupt
            ? styles.out
            : player.id === state.current_player_id
              ? styles.active
              : ''
          return (
            <li
              key={player.id}
              aria-label={`Player ${player.name}`}
              className={`${styles.player} ${stateClass}`}
              style={{ borderLeftColor: color }}
            >
              <span className={styles.disc} style={{ backgroundColor: color }} aria-hidden="true">
                {player.name.charAt(0).toUpperCase()}
              </span>
              <div className={styles.identity}>
                <strong>{player.name}</strong> {player.id === myPlayerId && <span className={styles.you}>(you)</span>}{' '}
                {player.id === state.current_player_id && <span className={styles.playing}>- playing</span>}
                {player.is_bankrupt && <span className={styles.bankrupt}>Bankrupt</span>}
              </div>
              <div className={styles.money}>
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
