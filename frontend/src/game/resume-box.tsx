import { useState } from 'react'
import type { PlayerSession } from '../session/player-session'
import { buildResumeLink } from '../session/resume-link'
import { ReadOnlyLink } from './read-only-link'

interface ResumeBoxProps {
  code: string
  session: PlayerSession
}

// The link carries the seat token, so it stays out of the page (and of screenshares) until asked for.
export function ResumeBox({ code, session }: ResumeBoxProps) {
  const [shown, setShown] = useState(false)

  return (
    <section aria-label="Private link">
      <h2>Private link</h2>
      <p>Continue on another device. Anyone with it can play as you; don't share it.</p>
      <button type="button" onClick={() => setShown((previous) => !previous)}>
        {shown ? 'Hide private link' : 'Show private link'}
      </button>
      {shown && <ReadOnlyLink label="Resume link" link={buildResumeLink(code, session)} />}
    </section>
  )
}
