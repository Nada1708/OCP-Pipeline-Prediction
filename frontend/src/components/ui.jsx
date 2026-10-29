import { AlertTriangle } from 'lucide-react'

export function Entete({ surtitre, titre, description, children }) {
  return (
    <div className="entete">
      <div>
        {surtitre && <div className="surtitre">{surtitre}</div>}
        <h1>{titre}</h1>
        {description && <p>{description}</p>}
      </div>
      {children}
    </div>
  )
}

export function Carte({ titre, description, action, children, className = '', style }) {
  return (
    <div className={`carte apparition ${className}`} style={style}>
      {(titre || action) && (
        <div className="carte-titre">
          <div>
            {titre && <h3>{titre}</h3>}
            {description && <p>{description}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  )
}

export function Kpi({ icone: Icone, label, valeur, unite, detail, chargement }) {
  return (
    <div className="carte kpi apparition">
      <div className="kpi-entete">
        <span>{label}</span>
        {Icone && <span className="kpi-icone"><Icone size={18} /></span>}
      </div>
      {chargement ? (
        <div className="squelette" style={{ height: 34, width: '60%', marginTop: 10 }} />
      ) : (
        <div className="kpi-valeur">
          {valeur}
          {unite && <span className="kpi-unite">{unite}</span>}
        </div>
      )}
      {detail && <div className="kpi-detail">{detail}</div>}
    </div>
  )
}

export function Badge({ classe = '', point, pulse, children }) {
  return (
    <span className={`badge ${classe}`}>
      {point && <span className={`point ${pulse ? 'pulse' : ''}`} />}
      {children}
    </span>
  )
}

export function Segmente({ options, valeur, onChange }) {
  return (
    <div className="segmente">
      {options.map(o => (
        <button key={o.valeur} className={valeur === o.valeur ? 'actif' : ''} onClick={() => onChange(o.valeur)}>
          {o.label}
        </button>
      ))}
    </div>
  )
}

export function Alerte({ children, info }) {
  return (
    <div className={`alerte ${info ? 'info' : ''}`}>
      <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: 1 }} />
      <div>{children}</div>
    </div>
  )
}

export function Squelette({ hauteur = 280 }) {
  return <div className="squelette" style={{ height: hauteur }} />
}

export function InfoBulle({ active, payload, label, formatLabel, formatValeur = (v) => v }) {
  if (!active || !payload?.length) return null
  return (
    <div className="tooltip">
      <div className="tooltip-titre">{formatLabel ? formatLabel(label) : label}</div>
      {payload.map(p => (
        <div key={p.dataKey?.toString() ?? p.name} className="tooltip-ligne">
          <i style={{ width: 8, height: 8, borderRadius: 2, background: p.color || p.stroke || p.fill, display: 'inline-block' }} />
          {p.name}
          <b>{formatValeur(p.value)}</b>
        </div>
      ))}
    </div>
  )
}
