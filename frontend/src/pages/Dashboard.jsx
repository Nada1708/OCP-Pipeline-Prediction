import { useEffect, useState } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, BarChart, Bar, ResponsiveContainer } from 'recharts'

function Dashboard() {
  const [historique, setHistorique] = useState([])
  const [debitHeure, setDebitHeure] = useState([])
  const [stats, setStats] = useState(null)

  useEffect(() => {
    axios.get('http://127.0.0.1:8000/historique?limit=100')
      .then(res => {
        const data = res.data.timestamps.map((t, i) => ({
          time: t.slice(5, 16),
          debit: res.data.debits[i]
        }))
        setHistorique(data)
      })

    axios.get('http://127.0.0.1:8000/debit-par-heure')
      .then(res => {
        const data = res.data.heures.map((h, i) => ({
          heure: `${h}h`,
          debit: res.data.debits[i]
        }))
        setDebitHeure(data)
      })

    axios.get('http://127.0.0.1:8000/stats')
      .then(res => setStats(res.data))
  }, [])

  return (
    <div style={{ padding: '30px' }}>

      <h2 style={{ color: '#00843D', borderBottom: '2px solid #00843D', paddingBottom: '10px' }}>
         Dashboard — Analyse des données
      </h2>

      {/* Stats */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '30px' }}>
          {[
            { label: 'Débit moyen', value: `${stats.debit_moyen} t/h` },
            { label: 'Débit max', value: `${stats.debit_max} t/h` },
            { label: 'Débit min', value: `${stats.debit_min} t/h` },
          ].map((s, i) => (
            <div key={i} style={{ background: 'white', padding: '15px', borderRadius: '10px', textAlign: 'center', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#00843D' }}>{s.value}</div>
              <div style={{ color: '#666' }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Graphe historique */}
      <div style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)', marginBottom: '20px' }}>
        <h3 style={{ color: '#00843D' }}> Historique du débit (100 dernières heures)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={historique}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" tick={{ fontSize: 10 }} interval={10} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="debit" stroke="#00843D" dot={false} name="Débit (t/h)" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Graphe par heure */}
      <div style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
        <h3 style={{ color: '#00843D' }}> Débit moyen par heure</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={debitHeure}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="heure" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="debit" fill="#00843D" name="Débit moyen (t/h)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

    </div>
  )
}

export default Dashboard