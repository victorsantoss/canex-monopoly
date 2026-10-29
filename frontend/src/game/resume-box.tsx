import type { PlayerSession } from '../session/player-session'
import { buildResumeLink } from '../session/resume-link'
import { ReadOnlyLink } from './read-only-link'

interface ResumeBoxProps {
  code: string
  session: PlayerSession
}

export function ResumeBox({ code, session }: ResumeBoxProps) {
  return (
    <section aria-label="Private link">
      <h2>Private link</h2>
      <p>Continue on another device. Anyone with it can play as you; don't share it.</p>
      <ReadOnlyLink label="Resume link" link={buildResumeLink(code, session)} />
    </section>
  )
}
