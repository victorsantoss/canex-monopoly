interface ReadOnlyLinkProps {
  label: string
  link: string
}

export function ReadOnlyLink({ label, link }: ReadOnlyLinkProps) {
  return <input aria-label={label} value={link} readOnly onFocus={(e) => e.target.select()} size={40} />
}
