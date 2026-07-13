import { useEffect, useState } from 'react'
import axios from 'axios'

function Accueil() {
  const [stats, setStats] = useState(null)
  const [performances, setPerformances] = useState(null)

  useEffect(() => {
    axios.get('http://127.0.0.1:8000/stats')
      .then(res => setStats(res.data))

    axios.get('http://127.0.0.1:8000/performances')
      .then(res => setPerformances(res.data))
  }, [])

  return (
    <div style={{ padding: '30px' }}>

      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #00843D, #005a2b)',
        padding: '30px',
        borderRadius: '10px',
        color: 'white',
        marginBottom: '30px'
      }}>
        <h1>🏭 OCP — Prédiction du Débit Horaire</h1>
        <p>Pipeline Khouribga → Jorf Lasfar | Système MLOps</p>
      </div>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '30px' }}>

        <div style={{ background: 'white', padding: '20px', borderRadius: '10px', borderLeft: '5px solid #00843D', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#00843D' }}>
            {performances ? performances.r2 : '...'}
          </div>
          <div style={{ color: '#666', marginTop: '5px' }}>R² du modèle</div>
        </div>

        <div style={{ background: 'white', padding: '20px', borderRadius: '10px', borderLeft: '5px solid #00843D', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#00843D' }}>
            {performances ? performances.mae : '...'}
          </div>
          <div style={{ color: '#666', marginTop: '5px' }}>MAE (t/h)</div>
        </div>

        <div style={{ background: 'white', padding: '20px', borderRadius: '10px', borderLeft: '5px solid #00843D', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#00843D' }}>
            {stats ? stats.nb_lignes : '...'}
          </div>
          <div style={{ color: '#666', marginTop: '5px' }}>Données d'entraînement</div>
        </div>

        <div style={{ background: 'white', padding: '20px', borderRadius: '10px', borderLeft: '5px solid #00843D', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#00843D' }}>
            8 mois
          </div>
          <div style={{ color: '#666', marginTop: '5px' }}>Historique</div>
        </div>

      </div>

      {/* Infos projet */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>

        <div style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
          <h3 style={{ color: '#00843D' }}>🎯 Objectif</h3>
          <p>Prédire le débit horaire (t/h) nécessaire à envoyer depuis Khouribga vers les clients de Jorf Lasfar.</p>
        </div>

        <div style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
          <h3 style={{ color: '#00843D' }}>👤 Projet</h3>
          <p><b>Stagiaire :</b> Nada Elaali</p>
          <p><b>Superviseur :</b> M. Othmane Salama</p>
          <p><b>Modèle :</b> XGBoost v3</p>
          <p><b>Méthode :</b> CRISP-DM + MLOps</p>
        </div>

      </div>

    </div>
  )
}

export default Accueil