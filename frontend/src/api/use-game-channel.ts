import { useEffect, useState } from 'react'
import type { GameEvent, GameState, GameUpdatedMessage } from './types'

export type ConnectionStatus = 'connecting' | 'open' | 'reconnecting'

export interface LoggedEvent {
  id: number
  event: GameEvent
}

export interface GameChannel {
  state: GameState | null
  eventLog: LoggedEvent[]
  connectionStatus: ConnectionStatus
  notFound: boolean
}

interface GameChannelOptions {
  reconnectDelayMs?: number
}

const UNKNOWN_GAME_CLOSE_CODE = 4404

function channelUrl(code: string): string {
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${scheme}://${location.host}/ws/games/${encodeURIComponent(code)}`
}

function parseMessage(data: unknown): GameUpdatedMessage | null {
  if (typeof data !== 'string') return null
  try {
    const message: unknown = JSON.parse(data)
    if (
      typeof message === 'object' &&
      message !== null &&
      'type' in message &&
      message.type === 'game_updated' &&
      'state' in message &&
      'events' in message &&
      Array.isArray(message.events)
    ) {
      return message as GameUpdatedMessage
    }
  } catch {
    // Malformed frame: the next snapshot repairs the screen anyway.
  }
  return null
}

// State is not reset when `code` changes: render the consumer with `key={code}` to watch another game.
export function useGameChannel(code: string, { reconnectDelayMs = 1500 }: GameChannelOptions = {}): GameChannel {
  const [state, setState] = useState<GameState | null>(null)
  const [eventLog, setEventLog] = useState<LoggedEvent[]>([])
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting')
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    let disposed = false
    let socket: WebSocket | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined
    let nextEventId = 0

    const connect = (): void => {
      socket = new WebSocket(channelUrl(code))
      socket.onopen = () => {
        if (!disposed) setConnectionStatus('open')
      }
      socket.onmessage = (message) => {
        const update = parseMessage(message.data)
        if (disposed || update === null) return
        setState(update.state)
        if (update.events.length > 0) {
          const logged = update.events.map((event) => ({ id: nextEventId++, event }))
          setEventLog((previous) => [...previous, ...logged])
        }
      }
      socket.onclose = (event) => {
        if (disposed) return
        if (event.code === UNKNOWN_GAME_CLOSE_CODE) {
          setNotFound(true)
          return
        }
        // Each connection starts with a full snapshot, so reconnecting resyncs; missed events are not replayed.
        setConnectionStatus('reconnecting')
        reconnectTimer = setTimeout(() => {
          setConnectionStatus('connecting')
          connect()
        }, reconnectDelayMs)
      }
    }

    connect()

    return () => {
      disposed = true
      clearTimeout(reconnectTimer)
      socket?.close()
    }
  }, [code, reconnectDelayMs])

  return { state, eventLog, connectionStatus, notFound }
}
