import { Link } from 'react-router-dom'
import type { GameState } from '../api/types'
import { useGameChannel } from '../api/use-game-channel'
import type { PlayerSession } from '../session/player-session'
import { Board } from './board'
import { EventLog } from './event-log'
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
      <Banner state={state} />
      {state.status === 'waiting' && <InviteBox code={state.code} />}
      <div className={styles.layout}>
        <Board state={state} />
        <aside className={styles.side}>
          <RollButton state={state} session={session} onSeatRejected={onSeatRejected} />
          <PlayersPanel state={state} myPlayerId={session.playerId} />
          <EventLog entries={eventLog} context={state} />
          <ResumeBox code={state.code} session={session} />
        </aside>
      </div>
    </main>
  )
}
