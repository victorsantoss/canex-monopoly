import { buildResumeLink, parseResumeFragment } from './resume-link'

describe('resume link', () => {
  it('carries the seat in the fragment, never in the query string', () => {
    const link = buildResumeLink('K7Q2XA', { playerId: 'p1', playerToken: 'secret token' })

    expect(link).toBe(`${location.origin}/games/K7Q2XA#player=p1&token=secret+token`)
    expect(new URL(link).search).toBe('')
  })

  it('reads back the seat it was built with', () => {
    const session = { playerId: 'p1', playerToken: 'a&b=c' }

    expect(parseResumeFragment(new URL(buildResumeLink('K7Q2XA', session)).hash)).toEqual(session)
  })

  it('parses a fragment with or without the leading #', () => {
    expect(parseResumeFragment('#player=p1&token=t')).toEqual({ playerId: 'p1', playerToken: 't' })
    expect(parseResumeFragment('player=p1&token=t')).toEqual({ playerId: 'p1', playerToken: 't' })
  })

  it('ignores extra parameters', () => {
    expect(parseResumeFragment('#foo=bar&player=p1&token=t')).toEqual({ playerId: 'p1', playerToken: 't' })
  })

  it.each([
    ['an empty fragment', ''],
    ['a bare #', '#'],
    ['a missing token', '#player=p1'],
    ['a missing player', '#token=t'],
    ['an empty token', '#player=p1&token='],
    ['an empty player', '#player=&token=t'],
  ])('returns null for %s', (_, fragment) => {
    expect(parseResumeFragment(fragment)).toBeNull()
  })
})
