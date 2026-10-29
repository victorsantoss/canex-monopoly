import { ReadOnlyLink } from './read-only-link'

interface InviteBoxProps {
  code: string
}

export function InviteBox({ code }: InviteBoxProps) {
  return (
    <section aria-label="Invite players">
      <h2>Invite players</h2>
      <p>
        Share this link, or the code <strong>{code}</strong>:
      </p>
      <ReadOnlyLink label="Invite link" link={`${location.origin}/games/${code}`} />
    </section>
  )
}
