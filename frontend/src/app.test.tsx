import { render, screen } from '@testing-library/react'
import { App } from './app'

describe('App', () => {
  it('renders the game title', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'Monopoly' })).toBeInTheDocument()
  })
})
