import { render, screen } from '@testing-library/react'
import { App } from './app'

describe('App', () => {
  it('opens on the lobby', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'Monopoly' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Create game' })).toBeInTheDocument()
  })
})
