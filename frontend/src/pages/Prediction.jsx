import { useState } from 'react'
import axios from 'axios'

function Prediction() {
  const [form, setForm] = useState({
    heure: new Date().getHours(),
    jour_semaine: new Date().getDay() === 0 ? 6 : new Date().getDay() - 1,
    mois: new Date().getMonth() + 1,
    jour_mois: new Date().getDate()
  })
  const [resultat, setResultat] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: parseInt(e.target.value) })
  }

  const predire = async () => {
    setLoading(true)
    try {
      const res = await axios.get('http://127.0.0.1:8000/predict-auto', {
        params: {
          heure: form.heure,
          jour_semaine: form.jour_semaine,
          mois: form.mois,
          jour_mois: form.jour_mois
        }
      })
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

  const jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
  const mois = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

  return (
    <div style={{ padding: '30px' }}>

      <h2 style={{ color: '#00843D', borderBottom: '2px solid #00843D', paddingBottom: '10px' }}>
        Prédiction du Débit Horaire
      </h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>

        <div style={{ background: 'white', padding: '30px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
          <h3 style={{ color: '#00843D', marginBottom: '20px' }}>Paramètres</h3>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', color: '#555', marginBottom: '8px', fontWeight: 'bold' }}>
              Heure de prédiction
            </label>
            <input
              type="number"
              name="heure"
              value={form.heure}
              onChange={handleChange}
              min={0} max={23}
              style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #ddd', fontSize: '1rem' }}
            />
            <small style={{ color: '#888' }}>Entre 0 (minuit) et 23</small>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', color: '#555', marginBottom: '8px', fontWeight: 'bold' }}>
              Jour de la semaine
            </label>
            <select
              name="jour_semaine"
              value={form.jour_semaine}
              onChange={handleChange}
              style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #ddd', fontSize: '1rem' }}
            >
              {jours.map((j, i) => (
                <option key={i} value={i}>{j}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', color: '#555', marginBottom: '8px', fontWeight: 'bold' }}>
              Mois
            </label>
            <select
              name="mois"
              value={form.mois}
              onChange={handleChange}
              style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #ddd', fontSize: '1rem' }}
            >
              {mois.map((m, i) => (
                <option key={i} value={i + 1}>{m}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '25px' }}>
            <label style={{ display: 'block', color: '#555', marginBottom: '8px', fontWeight: 'bold' }}>
              Jour du mois
            </label>
            <input
              type="number"
              name="jour_mois"
              value={form.jour_mois}
              onChange={handleChange}
              min={1} max={31}
              style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #ddd', fontSize: '1rem' }}
            />
          </div>

          <button
            onClick={predire}
            disabled={loading}
            style={{
              width: '100%', padding: '14px',
              background: loading ? '#888' : '#00843D',
              color: 'white', border: 'none',
              borderRadius: '8px', fontSize: '1.1rem',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: 'bold'
            }}
          >
            {loading ? 'Calcul en cours...' : 'Prédire le débit'}
          </button>
        </div>

        <div style={{ background: 'white', padding: '30px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
          <h3 style={{ color: '#00843D', marginBottom: '20px' }}>Résultat</h3>

          {resultat ? (
            <div>
              <div style={{
                background: `linear-gradient(135deg, ${couleurStatut[resultat.statut]}, #005a2b)`,
                padding: '50px', borderRadius: '15px',
                textAlign: 'center', color: 'white', margin: '20px 0'
              }}>
                <div style={{ fontSize: '1rem', opacity: 0.8, marginBottom: '10px' }}>Débit prédit</div>
                <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '4rem', fontWeight: 'bold' }}>{resultat.debit_predit}</span>
                  <span style={{ fontSize: '2rem' }}>t/h</span>
                </div>
              </div>

              <div style={{
                padding: '15px', borderRadius: '8px', textAlign: 'center',
                background: couleurStatut[resultat.statut] + '20',
                border: `2px solid ${couleurStatut[resultat.statut]}`
              }}>
                <b style={{ color: couleurStatut[resultat.statut], fontSize: '1.1rem' }}>
                  {resultat.statut === 'eleve' && 'Débit élevé — Production optimale'}
                  {resultat.statut === 'normal' && 'Débit normal — Production standard'}
                  {resultat.statut === 'faible' && 'Débit faible — Vérifier le pipeline'}
                </b>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '80px', color: '#888' }}>
              <div style={{ fontSize: '4rem', marginBottom: '20px' }}></div>
              <p style={{ fontSize: '1.1rem' }}>
                Sélectionnez les paramètres<br />et cliquez sur Prédire
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}

export default Prediction