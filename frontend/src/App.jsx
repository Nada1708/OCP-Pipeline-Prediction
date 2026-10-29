import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { Menu, Database } from 'lucide-react'
import Navbar from './components/Navbar'
import { LIENS } from './navigation'
import { Badge } from './components/ui'
import { api, formatDateHeure } from './api'
import Accueil from './pages/Accueil'
import Dashboard from './pages/Dashboard'
import Prediction from './pages/Prediction'
import Performances from './pages/Performances'
import Qualite from './pages/Qualite'

function Topbar({ ouvrirMenu }) {
  const { pathname } = useLocation()
  const [etat, setEtat] = useState({ enLigne: null, derniere: null })
  const titre = LIENS.find(l => l.path === pathname)?.label ?? ''

  useEffect(() => {
    api.get('/stats')
      .then(res => setEtat({ enLigne: true, derniere: res.data.derniere_date }))
      .catch(() => setEtat({ enLigne: false, derniere: null }))
  }, [])

  return (
    <header className="topbar">
      <button className="menu-bouton" onClick={ouvrirMenu} aria-label="Menu"><Menu size={20} /></button>
      <div className="topbar-titre">{titre}</div>
      <div className="topbar-droite">
        {etat.derniere && (
          <Badge classe="neutre badge-large"><Database size={13} /> Dernière mesure : {formatDateHeure(etat.derniere)}</Badge>
        )}
        {etat.enLigne === true && <Badge point pulse>API en ligne</Badge>}
        {etat.enLigne === false && <Badge classe="rouge" point>API hors ligne</Badge>}
      </div>
    </header>
  )
}

function App() {
  const [menuOuvert, setMenuOuvert] = useState(false)

  return (
    <BrowserRouter>
      <div className="app">
        <Navbar ouverte={menuOuvert} fermer={() => setMenuOuvert(false)} />
        <main className="contenu">
          <Topbar ouvrirMenu={() => setMenuOuvert(true)} />
          <div className="page">
            <Routes>
              <Route path="/" element={<Accueil />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/prediction" element={<Prediction />} />
              <Route path="/performances" element={<Performances />} />
              <Route path="/qualite" element={<Qualite />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
