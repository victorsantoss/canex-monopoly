import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { GamePage } from './pages/game-page'
import { LobbyPage } from './pages/lobby-page'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LobbyPage />} />
        <Route path="/games/:code" element={<GamePage />} />
        <Route path="*" element={<LobbyPage />} />
      </Routes>
    </BrowserRouter>
  )
}
