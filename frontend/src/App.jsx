import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Accueil from './pages/Accueil'
import Dashboard from './pages/Dashboard'
import Prediction from './pages/Prediction'
import Performances from './pages/Performances'

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Accueil />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/prediction" element={<Prediction />} />
        <Route path="/performances" element={<Performances />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App