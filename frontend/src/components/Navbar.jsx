import { NavLink } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import { LIENS } from '../navigation'

function Navbar({ ouverte, fermer }) {
  return (
    <>
      <div className={`voile ${ouverte ? 'visible' : ''}`} onClick={fermer} />
      <aside className={`sidebar ${ouverte ? 'ouverte' : ''}`}>
        <div className="sidebar-logo">
          <img src="/images/ocp_logo.png" alt="OCP" />
        </div>
        <div className="sidebar-sous-titre">Khouribga → Jorf Lasfar</div>

        <div className="sidebar-section">Navigation</div>
        <nav>
          {LIENS.map(({ path, label, desc, icone: Icone }) => (
            <NavLink
              key={path}
              to={path}
              end
              onClick={fermer}
              className={({ isActive }) => `nav-lien ${isActive ? 'actif' : ''}`}
            >
              <Icone size={19} />
              <span>
                {label}
                <span className="nav-desc">{desc}</span>
              </span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-pied">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'white', fontWeight: 600, marginBottom: 4 }}>
            <ShieldCheck size={16} /> Système MLOps
          </div>
          Prévision du débit horaire · PFE 2026
        </div>
      </aside>
    </>
  )
}

export default Navbar
