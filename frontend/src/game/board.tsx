import type { CSSProperties, ReactNode } from 'react'
import type { GameState, Square } from '../api/types'
import styles from './board.module.scss'
import { playerColor, priceGroup, ringCell, ringSide } from './game-view'

interface BoardProps {
  state: GameState
  children?: ReactNode
}

const GROUP_CLASSES = [styles.group0, styles.group1, styles.group2, styles.group3, styles.group4, styles.group5]

function squareClass(square: Square): string {
  if (square.kind === 'start') return `${styles.square} ${styles.start}`
  if (square.kind === 'empty' || square.price === null) return `${styles.square} ${styles.empty}`
  const owned = square.owner_id === null ? '' : ` ${styles.owned}`
  return `${styles.square} ${styles.property} ${GROUP_CLASSES[priceGroup(square.price)]}${owned}`
}

export function Board({ state, children }: BoardProps) {
  const { board, players } = state
  const side = ringSide(board.length)
  // The centre panel is sized from the ring's side count, so the count is handed to the stylesheet.
  const ringStyle = { '--side': side } as CSSProperties

  return (
    <div className={styles.table} style={ringStyle}>
      <ol className={styles.board} aria-label="Board">
        {board.map((square) => {
          const cell = ringCell(square.index, board.length)
          const occupants = players.filter((player) => !player.is_bankrupt && player.position === square.index)
          return (
            <li
              key={square.index}
              aria-label={`Square ${square.index}: ${square.name}`}
              className={squareClass(square)}
              style={
                {
                  gridRow: cell.row,
                  gridColumn: cell.column,
                  '--owner': playerColor(players, square.owner_id),
                } as CSSProperties
              }
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
      <div className={styles.centre}>
        <span className={styles.plate} data-code={state.code} aria-hidden="true" />
        {children}
      </div>
    </div>
  )
}
