import { loadPlayerSession, savePlayerSession } from './player-session'

describe('player session', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.restoreAllMocks()
  })

  it('returns null when nothing was saved for the game', () => {
    expect(loadPlayerSession('K7Q2XA')).toBeNull()
  })

  it('keeps one session per game code', () => {
    savePlayerSession('K7Q2XA', { playerId: 'p1', playerToken: 'secret-1' })
    savePlayerSession('ABCDEF', { playerId: 'p2', playerToken: 'secret-2' })

    expect(loadPlayerSession('K7Q2XA')).toEqual({ playerId: 'p1', playerToken: 'secret-1' })
    expect(loadPlayerSession('ABCDEF')).toEqual({ playerId: 'p2', playerToken: 'secret-2' })
  })

  it('ignores a corrupted entry', () => {
    sessionStorage.setItem('monopoly.session.K7Q2XA', '{not json')

    expect(loadPlayerSession('K7Q2XA')).toBeNull()
  })

  it('ignores an entry with the wrong shape', () => {
    sessionStorage.setItem('monopoly.session.K7Q2XA', JSON.stringify({ playerId: 1 }))

    expect(loadPlayerSession('K7Q2XA')).toBeNull()
  })

  it('does not throw when storage is unavailable', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })

    expect(() => savePlayerSession('K7Q2XA', { playerId: 'p1', playerToken: 't' })).not.toThrow()
    expect(loadPlayerSession('K7Q2XA')).toBeNull()
  })
})
