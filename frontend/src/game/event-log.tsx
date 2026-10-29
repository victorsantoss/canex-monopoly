import type { LoggedEvent } from '../api/use-game-channel'
import { describeEvent, type EventContext } from '../events/describe-event'

interface EventLogProps {
  entries: LoggedEvent[]
  context: EventContext
}

export function EventLog({ entries, context }: EventLogProps) {
  const latestFirst = [...entries].reverse()

  return (
    <section aria-label="Event log">
      <h2>Events</h2>
      {latestFirst.length === 0 ? (
        <p>Nothing happened yet.</p>
      ) : (
        <ol>
          {latestFirst.map((entry) => (
            <li key={entry.id}>{describeEvent(entry.event, context)}</li>
          ))}
        </ol>
      )}
    </section>
  )
}
