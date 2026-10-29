import type { GameState } from '../api/types'
import styles from './board.module.scss'
import { playerColor, ringCell, ringSide } from './game-view'

interface BoardProps {
  state: GameState
}

export function Board({ state }: BoardProps) {
  const { board, players } = state
  const side = ringSide(board.length)

  return (
    <ol className={styles.board} style={{ gridTemplateColumns: `repeat(${side}, 1fr)` }} aria-label="Board">
      {board.map((square) => {
        const cell = ringCell(square.index, board.length)
        const occupants = players.filter((player) => !player.is_bankrupt && player.position === square.index)
        return (
          <li
            key={square.index}
            aria-label={`Square ${square.index}: ${square.name}`}
            className={styles.square}
            style={{
              gridRow: cell.row,
              gridColumn: cell.column,
              borderTopColor: playerColor(players, square.owner_id),
            }}
          >
            <span className={styles.name}>{square.name}</span>
            {square.kind === 'property' && (
              <span className={styles.prices}>
                Price {square.price} / Rent {square.rent}
              </span>
            )}
            <span className={styles.tokens}>
              {occupants.map((player) => (
                <span
                  key={player.id}
                  title={player.name}
                  className={player.id === state.current_player_id ? `${styles.token} ${styles.active}` : styles.token}
                  style={{ backgroundColor: playerColor(players, player.id) }}
                >
                  {player.name.charAt(0).toUpperCase()}
                </span>
              ))}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
