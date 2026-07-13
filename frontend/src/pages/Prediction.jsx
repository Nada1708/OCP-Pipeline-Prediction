import { useState } from 'react'
import axios from 'axios'

function Prediction() {
  const [form, setForm] = useState({
    heure: 8, jour_semaine: 0, mois: 6, jour_mois: 15,
    est_weekend: 0, lag_1h: 1500, lag_2h: 1480, lag_3h: 1460,
    lag_6h: 1450, lag_12h: 1440, lag_24h: 1500,
    rolling_3h: 1480, rolling_6h: 1470, rolling_12h: 1460,
    rolling_24h: 1450, std_6h: 30, vente_heure: 2500,
    lag_48h: 1490, lag_168h: 1500, diff_1h: 20, diff_24h: 0
  })
  const [resultat, setResultat] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: parseFloat(e.target.value) })
  }

  const predire = async () => {
    setLoading(true)
    try {
      const res = await axios.post('http://127.0.0.1:8000/predict', form)
      setResultat(res.data)
    } catch {
      alert('Erreur de prédiction')
    }
    setLoading(false)
  }

  const couleurStatut = {
    eleve: '#00843D',
    normal: '#2196F3',
    faible: '#FFC107'
  }

  return (
    <div style={{ padding: '30px' }}>

      <h2 style={{ color: '#00843D', borderBottom: '2px solid #00843D', paddingBottom: '10px' }}>
        🔮 Prédiction du Débit Horaire
      </h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>

        {/* Formulaire */}
        <div style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
          <h3 style={{ color: '#00843D' }}>⚙️ Paramètres</h3>

          {[
            { label: 'Heure (0-23)', name: 'heure', min: 0, max: 23 },
            { label: 'Jour semaine (0=Lundi, 6=Dimanche)', name: 'jour_semaine', min: 0, max: 6 },
            { label: 'Mois (1-12)', name: 'mois', min: 1, max: 12 },
            { label: 'Débit il y a 1h (t/h)', name: 'lag_1h', min: 0, max: 3000 },
            { label: 'Débit il y a 24h (t/h)', name: 'lag_24h', min: 0, max: 3000 },
            { label: 'Débit il y a 48h (t/h)', name: 'lag_48h', min: 0, max: 3000 },
            { label: 'Débit il y a 168h (t/h)', name: 'lag_168h', min: 0, max: 3000 },
            { label: 'Moyenne 3h (t/h)', name: 'rolling_3h', min: 0, max: 3000 },
            { label: 'Vente/heure (TSM)', name: 'vente_heure', min: 0, max: 5000 },
          ].map((field) => (
            <div key={field.name} style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#555', marginBottom: '4px' }}>
                {field.label}
              </label>
              <input
                type="number"
                name={field.name}
                value={form[field.name]}
                onChange={handleChange}
                min={field.min}
                max={field.max}
                style={{
                  width: '100%', padding: '8px', borderRadius: '6px',
                  border: '1px solid #ddd', fontSize: '0.9rem'
                }}
              />
            </div>
          ))}

          <button
            onClick={predire}
            disabled={loading}
            style={{
              width: '100%', padding: '12px',
              background: loading ? '#888' : '#00843D',
              color: 'white', border: 'none',
              borderRadius: '8px', fontSize: '1rem',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '10px'
            }}
          >
            {loading ? 'Calcul en cours...' : '🔮 Prédire le débit'}
          </button>
        </div>

        {/* Résultat */}
        <div style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
          <h3 style={{ color: '#00843D' }}>📊 Résultat</h3>

          {resultat ? (
            <div>
              <div style={{
                background: `linear-gradient(135deg, ${couleurStatut[resultat.statut]}, #005a2b)`,
                padding: '40px', borderRadius: '15px',
                textAlign: 'center', color: 'white', margin: '20px 0'
              }}>
                <div style={{ fontSize: '1rem', opacity: 0.8 }}>Débit prédit</div>
                <div style={{ fontSize: '3rem', fontWeight: 'bold' }}>
                  {resultat.debit_predit}
                </div>
                <div style={{ fontSize: '1.2rem' }}>t/h</div>
              </div>

              <div style={{
                padding: '15px', borderRadius: '8px', textAlign: 'center',
                background: couleurStatut[resultat.statut] + '20',
                border: `2px solid ${couleurStatut[resultat.statut]}`
              }}>
                <b style={{ color: couleurStatut[resultat.statut] }}>
                  {resultat.statut === 'eleve' && '🟢 Débit élevé — Production optimale'}
                  {resultat.statut === 'normal' && '🔵 Débit normal — Production standard'}
                  {resultat.statut === 'faible' && '🟡 Débit faible — Vérifier le pipeline'}
                </b>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '80px', color: '#888' }}>
              <div style={{ fontSize: '3rem' }}>🔮</div>
              <p>Remplissez les paramètres<br />et cliquez sur Prédire</p>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}

export default Prediction