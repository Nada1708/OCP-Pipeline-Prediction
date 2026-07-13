import { useEffect, useState } from 'react'
import axios from 'axios'

function Performances() {
  const [perf, setPerf] = useState(null)

  useEffect(() => {
    axios.get('http://127.0.0.1:8000/performances')
      .then(res => setPerf(res.data))
  }, [])

  return (
    <div style={{ padding: '30px' }}>

      <h2 style={{ color: '#00843D', borderBottom: '2px solid #00843D', paddingBottom: '10px' }}>
        📈 Performances du modèle
      </h2>

      {perf ? (
        <>
          {/* Métriques */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '30px' }}>
            {[
              { label: 'R²', value: perf.r2, desc: 'Coefficient de détermination' },
              { label: 'MAE', value: `${perf.mae} t/h`, desc: 'Erreur absolue moyenne' },
              { label: 'RMSE', value: `${perf.rmse} t/h`, desc: 'Erreur quadratique moyenne' },
            ].map((m, i) => (
              <div key={i} style={{
                background: 'white', padding: '25px', borderRadius: '10px',
                textAlign: 'center', boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
                borderTop: '4px solid #00843D'
              }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#00843D' }}>{m.value}</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>{m.label}</div>
                <div style={{ color: '#888', fontSize: '0.85rem' }}>{m.desc}</div>
              </div>
            ))}
          </div>

          {/* Comparaison baseline */}
          <div style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)', marginBottom: '20px' }}>
            <h3 style={{ color: '#00843D' }}>📊 Comparaison avec le baseline</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#00843D', color: 'white' }}>
                  <th style={{ padding: '10px' }}>Version</th>
                  <th style={{ padding: '10px' }}>R²</th>
                  <th style={{ padding: '10px' }}>MAE (t/h)</th>
                  <th style={{ padding: '10px' }}>RMSE (t/h)</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { version: 'Baseline', r2: '0.70', mae: '84.23', rmse: '144.12' },
                  { version: 'XGBoost V2', r2: '0.73', mae: '78.66', rmse: '134.86' },
                  { version: 'XGBoost V3 ✅', r2: perf.r2, mae: perf.mae, rmse: perf.rmse },
                ].map((row, i) => (
                  <tr key={i} style={{
                    background: i === 2 ? '#e8f5e9' : i % 2 === 0 ? '#f9f9f9' : 'white',
                    fontWeight: i === 2 ? 'bold' : 'normal'
                  }}>
                    <td style={{ padding: '10px', textAlign: 'center' }}>{row.version}</td>
                    <td style={{ padding: '10px', textAlign: 'center', color: '#00843D' }}>{row.r2}</td>
                    <td style={{ padding: '10px', textAlign: 'center' }}>{row.mae}</td>
                    <td style={{ padding: '10px', textAlign: 'center' }}>{row.rmse}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Infos modèle */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
              <h3 style={{ color: '#00843D' }}>🤖 Informations modèle</h3>
              <p><b>Modèle :</b> {perf.modele}</p>
              <p><b>Taille train :</b> {perf.train_size} lignes</p>
              <p><b>Taille test :</b> {perf.test_size} lignes</p>
              <p><b>Validation :</b> Split temporel 80/20</p>
              <p><b>Data leakage :</b> ✅ Vérifié et corrigé</p>
            </div>

            <div style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
              <h3 style={{ color: '#00843D' }}>⚙️ Hyperparamètres</h3>
              <p><b>learning_rate :</b> 0.01</p>
              <p><b>max_depth :</b> 4</p>
              <p><b>n_estimators :</b> 1000</p>
              <p><b>subsample :</b> 0.7</p>
              <p><b>early_stopping :</b> 50</p>
            </div>
          </div>
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '80px', color: '#888' }}>
          <p>Chargement des performances...</p>
        </div>
      )}
    </div>
  )
}

export default Performances