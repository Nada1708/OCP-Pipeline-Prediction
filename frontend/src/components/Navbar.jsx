import { Link, useLocation } from 'react-router-dom'

function Navbar() {
  const location = useLocation()

  return (
    <nav style={{
      background: '#00843D',
      padding: '15px 30px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>

      {/* Logo */}
      <div style={{ color: 'white', fontSize: '1.2rem', fontWeight: 'bold' }}>
        🏭 OCP Pipeline
      </div>

      {/* Liens */}
      <div style={{ display: 'flex', gap: '20px' }}>
        {[
          { path: '/', label: 'Accueil' },
          { path: '/dashboard', label: 'Dashboard' },
          { path: '/prediction', label: 'Prédiction' },
          { path: '/performances', label: 'Performances' },
        ].map((item) => (
          <Link
            key={item.path}
            to={item.path}
            style={{
              color: location.pathname === item.path ? '#FFD700' : 'white',
              textDecoration: 'none',
              fontWeight: location.pathname === item.path ? 'bold' : 'normal'
            }}
          >
            {item.label}
          </Link>
        ))}
      </div>

    </nav>
  )
}

export default Navbar