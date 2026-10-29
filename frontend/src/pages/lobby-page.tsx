import { useNavigate } from 'react-router-dom'
import type { JoinedGame } from '../api/types'
import { CreateGameForm } from '../lobby/create-game-form'
import { JoinGameForm } from '../lobby/join-game-form'
import { savePlayerSession } from '../session/player-session'
import styles from './lobby-page.module.scss'

export function LobbyPage() {
  const navigate = useNavigate()

  const enterGame = (joined: JoinedGame): void => {
    savePlayerSession(joined.code, { playerId: joined.player_id, playerToken: joined.player_token })
    navigate(`/games/${joined.code}`)
  }

  return (
    <main className={styles.lobby}>
      <h1>Monopoly</h1>
      <div className={styles.forms}>
        <CreateGameForm onJoined={enterGame} />
        <JoinGameForm onJoined={enterGame} />
      </div>
    </main>
  )
}
