import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Accueil from './pages/Accueil'
import Dashboard from './pages/Dashboard'
import Prediction from './pages/Prediction'
import Performances from './pages/Performances'

function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex' }}>
        <Navbar />
        <div style={{ marginLeft: '250px', width: 'calc(100vw - 250px)', minHeight: '100vh', background: '#f5f5f5', overflowX: 'hidden' }}>
          <Routes>
            <Route path="/" element={<Accueil />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/prediction" element={<Prediction />} />
            <Route path="/performances" element={<Performances />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}

export default App