interface InviteBoxProps {
  code: string
}

export function InviteBox({ code }: InviteBoxProps) {
  const link = `${location.origin}/games/${code}`

  return (
    <section aria-label="Invite players">
      <h2>Invite players</h2>
      <p>
        Share this link, or the code <strong>{code}</strong>:
      </p>
      <input aria-label="Invite link" value={link} readOnly onFocus={(e) => e.target.select()} size={40} />
    </section>
  )
}
