import { Link, useLocation } from 'react-router-dom'

function Navbar() {
  const location = useLocation()

  return (
    <div style={{
      width: '250px',
      minHeight: '100vh',
      background: 'white',
      borderRight: '2px solid #e0e0e0',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '20px 0',
      position: 'fixed',
      left: 0,
      top: 0,
      boxShadow: '2px 0 10px rgba(0,0,0,0.1)'
    }}>

      {/* Logo OCP */}
      <img
        src="/images/ocp_logo.png"
        alt="OCP Logo"
        style={{ height: '50px', objectFit: 'contain', marginBottom: '30px' }}
      />

      <hr style={{ width: '80%', border: '1px solid #e0e0e0', marginBottom: '20px' }} />

      {/* Liens */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%' }}>
        {[
          { path: '/', label: ' Accueil' },
          { path: '/dashboard', label: 'Dashboard' },
          { path: '/prediction', label: 'Prédiction' },
          { path: '/performances', label: ' Performances' },
        ].map((item) => (
          <Link
            key={item.path}
            to={item.path}
            style={{
              color: location.pathname === item.path ? '#00843D' : 'black',
              textDecoration: 'none',
              fontWeight: location.pathname === item.path ? 'bold' : 'normal',
              fontSize: '0.95rem',
              padding: '10px 20px',
              background: location.pathname === item.path ? '#e8f5e9' : 'transparent',
              borderLeft: location.pathname === item.path ? '4px solid #00843D' : '4px solid transparent',
            }}
          >
            {item.label}
          </Link>
        ))}
      </div>

    </div>
  )
}

export default Navbar