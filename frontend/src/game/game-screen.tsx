import { Link } from 'react-router-dom'
import type { GameState } from '../api/types'
import { useGameChannel } from '../api/use-game-channel'
import type { PlayerSession } from '../session/player-session'
import { Board } from './board'
import { EventLog } from './event-log'
import { describeSettings, lastDiceRoll } from './game-view'
import styles from './game-screen.module.scss'
import { InviteBox } from './invite-box'
import { PlayersPanel } from './players-panel'
import { ResumeBox } from './resume-box'
import { RollButton } from './roll-button'

interface GameScreenProps {
  code: string
  session: PlayerSession
  onSeatRejected: () => void
}

// Purely visual: the roll is announced in words by the event log.
function Die({ value }: { value: number }) {
  return (
    <span className={styles.die} data-value={value} aria-hidden="true">
      {Array.from({ length: 9 }, (_, slot) => (
        <span key={slot} className={styles.pip} />
      ))}
    </span>
  )
}

function Banner({ state }: { state: GameState }) {
  if (state.status === 'waiting') {
    return (
      <p className={styles.banner}>
        {state.players.length}/{state.seats} players joined
      </p>
    )
  }
  if (state.status === 'finished') {
    const winner = state.players.find((player) => player.id === state.winner_id)
    return (
      <p role="status" className={`${styles.banner} ${styles.winner}`}>
        {winner?.name ?? 'Nobody'} wins!
      </p>
    )
  }
  return null
}

export function GameScreen({ code, session, onSeatRejected }: GameScreenProps) {
  const { state, eventLog, connectionStatus, notFound } = useGameChannel(code)
  const lastRoll = lastDiceRoll(eventLog)

  if (notFound) {
    return (
      <main className={styles.screen}>
        <p>This game does not exist.</p>
        <Link to="/">Back to the lobby</Link>
      </main>
    )
  }

  if (state === null) {
    return (
      <main className={styles.screen}>
        <p>Connecting to game {code}...</p>
      </main>
    )
  }

  return (
    <main className={styles.screen}>
      <header className={styles.header}>
        <h1>Game {state.code}</h1>
        {connectionStatus !== 'open' && <span className={styles.connection}>Reconnecting...</span>}
      </header>
      <p className={styles.settings}>{describeSettings(state.settings)}</p>
      {state.status === 'waiting' && (
        <div className={styles.invite}>
          <InviteBox code={state.code} />
        </div>
      )}
      <div className={styles.layout}>
        <Board state={state}>
          <Banner state={state} />
          {lastRoll !== null && <Die value={lastRoll} />}
        </Board>
        <aside className={styles.side}>
          <RollButton
            state={state}
            session={session}
            connectionStatus={connectionStatus}
            onSeatRejected={onSeatRejected}
          />
          <PlayersPanel state={state} myPlayerId={session.playerId} />
          <EventLog entries={eventLog} context={state} />
          <ResumeBox code={state.code} session={session} />
        </aside>
      </div>
    </main>
  )
}
