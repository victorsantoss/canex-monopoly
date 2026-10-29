import type { PlayerSession } from '../session/player-session'
import { buildResumeLink } from '../session/resume-link'

interface ResumeBoxProps {
  code: string
  session: PlayerSession
}

export function ResumeBox({ code, session }: ResumeBoxProps) {
  const link = buildResumeLink(code, session)

  return (
    <section aria-label="Private link">
      <h2>Private link</h2>
      <p>Continue on another device. Anyone with it can play as you; don't share it.</p>
      <input aria-label="Resume link" value={link} readOnly onFocus={(e) => e.target.select()} size={40} />
    </section>
  )
}
