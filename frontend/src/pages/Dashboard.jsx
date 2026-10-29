import { useEffect, useState } from 'react'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Activity, TrendingUp, TrendingDown, Gauge } from 'lucide-react'
import { api, COULEURS, COULEURS_CLIENTS, formatNombre, messageErreur } from '../api'
import { Entete, Carte, Kpi, Segmente, Alerte, Squelette, InfoBulle } from '../components/ui'

const PERIODES = [
  { valeur: 24, label: '24 h' },
  { valeur: 168, label: '7 jours' },
  { valeur: 720, label: '30 jours' },
]

// Echelle sequentielle vert clair -> vert fonce
const couleurHeatmap = (v, min, max) => {
  const t = Math.max(0, Math.min(1, (v - min) / (max - min || 1)))
  const de = [231, 244, 236], a = [0, 97, 45]
  return `rgb(${de.map((c, i) => Math.round(c + (a[i] - c) * t)).join(',')})`
}

function Heatmap({ profil }) {
  const toutes = profil.valeurs.flat()
  const min = Math.min(...toutes), max = Math.max(...toutes)
  return (
    <>
      <div className="tableau-conteneur">
        <div className="heatmap">
          <span />
          {profil.heures.map(h => <span key={h} className="heatmap-heure">{h % 3 === 0 ? `${h}h` : ''}</span>)}
          {profil.jours.map((j, i) => (
            <div key={j} style={{ display: 'contents' }}>
              <span className="heatmap-label">{j}</span>
              {profil.valeurs[i].map((v, h) => (
                <div key={h} className="heatmap-cellule" style={{ background: couleurHeatmap(v, min, max) }}
                  title={`${j} ${h}h : ${formatNombre(v)} t/h`} />
              ))}
            </div>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 14, fontSize: '0.78rem', color: 'var(--texte-3)' }}>
        <span className="num">{formatNombre(min)} t/h</span>
        <div style={{ flex: 1, maxWidth: 220, height: 8, borderRadius: 4, background: `linear-gradient(90deg, ${couleurHeatmap(min, min, max)}, ${couleurHeatmap(max, min, max)})` }} />
        <span className="num">{formatNombre(max)} t/h</span>
      </div>
    </>
  )
}

function Dashboard() {
  const [periode, setPeriode] = useState(168)
  const [historique, setHistorique] = useState(null)
  const [stats, setStats] = useState(null)
  const [parHeure, setParHeure] = useState(null)
  const [profil, setProfil] = useState(null)
  const [clients, setClients] = useState(null)
  const [erreur, setErreur] = useState(null)

  useEffect(() => {
    api.get('/historique', { params: { limit: periode } })
      .then(res => setHistorique(res.data.timestamps.map((t, i) => ({ date: t, debit: res.data.debits[i] }))))
      .catch(err => setErreur(messageErreur(err)))
  }, [periode])

  useEffect(() => {
    const echec = err => setErreur(messageErreur(err))
    api.get('/stats').then(res => setStats(res.data)).catch(echec)
    api.get('/debit-par-heure').then(res => setParHeure(res.data.heures.map((h, i) => ({ heure: `${h}h`, debit: res.data.debits[i] })))).catch(echec)
    api.get('/profil-semaine').then(res => setProfil(res.data)).catch(echec)
    api.get('/repartition-clients', { params: { jours: 30 } }).then(res => setClients(res.data)).catch(echec)
  }, [])

  const formatAxe = (iso) => {
    const d = new Date(iso)
    return periode <= 24
      ? d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      : d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
  }

  return (
    <>
      <Entete surtitre="Analyse des données" titre="Dashboard"
        description="Historique du débit total distribué, profils horaires et hebdomadaires, et répartition par client." />

      {erreur && <div className="espace"><Alerte>{erreur}</Alerte></div>}

      <div className="grille grille-kpi">
        <Kpi icone={Activity} label="Dernier débit" valeur={formatNombre(stats?.dernier_debit)} unite="t/h" chargement={!stats} detail="Dernière mesure disponible" />
        <Kpi icone={Gauge} label="Débit moyen" valeur={formatNombre(stats?.debit_moyen)} unite="t/h" chargement={!stats} detail="Hors arrêts opérationnels" />
        <Kpi icone={TrendingUp} label="Débit maximal" valeur={formatNombre(stats?.debit_max)} unite="t/h" chargement={!stats} detail={stats?.periode} />
        <Kpi icone={TrendingDown} label="Débit minimal" valeur={formatNombre(stats?.debit_min)} unite="t/h" chargement={!stats} detail="Au-dessus du seuil d'arrêt (500 t/h)" />
      </div>

      <Carte className="espace" titre="Historique du débit total" description="Mesures horaires les plus récentes"
        action={<Segmente options={PERIODES} valeur={periode} onChange={setPeriode} />}>
        {historique ? (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={historique} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="degradeHisto" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={COULEURS.modele} stopOpacity={0.25} />
                  <stop offset="100%" stopColor={COULEURS.modele} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={COULEURS.grille} vertical={false} />
              <XAxis dataKey="date" tickFormatter={formatAxe} tick={{ fill: COULEURS.axe, fontSize: 11 }} minTickGap={50} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: COULEURS.axe, fontSize: 11 }} axisLine={false} tickLine={false} width={50} />
              <Tooltip content={<InfoBulle formatLabel={(d) => new Date(d).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })} formatValeur={(v) => `${formatNombre(v)} t/h`} />} />
              {stats && <ReferenceLine y={stats.debit_moyen} stroke={COULEURS.moyenne} strokeDasharray="4 4" label={{ value: 'Moyenne', fill: COULEURS.moyenne, fontSize: 11, position: 'insideTopRight' }} />}
              <Area isAnimationActive={false} type="monotone" dataKey="debit" stroke={COULEURS.modele} strokeWidth={2} fill="url(#degradeHisto)" name="Débit" />
            </AreaChart>
          </ResponsiveContainer>
        ) : <Squelette hauteur={320} />}
      </Carte>

      <div className="grille grille-2 espace">
        <Carte titre="Profil hebdomadaire" description="Débit moyen selon le jour et l'heure">
          {profil ? <Heatmap profil={profil} /> : <Squelette hauteur={220} />}
        </Carte>

        <Carte titre="Débit moyen par heure" description="Toutes journées confondues">
          {parHeure ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={parHeure} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid stroke={COULEURS.grille} vertical={false} />
                <XAxis dataKey="heure" tick={{ fill: COULEURS.axe, fontSize: 11 }} interval={2} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: COULEURS.axe, fontSize: 11 }} axisLine={false} tickLine={false} width={50} domain={['dataMin - 100', 'auto']} tickFormatter={(v) => formatNombre(v)} />
                <Tooltip cursor={{ fill: 'var(--vert-pale)' }} content={<InfoBulle formatValeur={(v) => `${formatNombre(v)} t/h`} />} />
                <Bar isAnimationActive={false} dataKey="debit" fill={COULEURS.modele} radius={[4, 4, 0, 0]} name="Débit moyen" />
              </BarChart>
            </ResponsiveContainer>
          ) : <Squelette hauteur={250} />}
        </Carte>
      </div>

      <Carte titre="Volume journalier par client" description="30 derniers jours, en milliers de tonnes par jour">
        {clients ? (
          <>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={clients.journalier} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid stroke={COULEURS.grille} vertical={false} />
                <XAxis dataKey="date" tickFormatter={(d) => new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
                  tick={{ fill: COULEURS.axe, fontSize: 11 }} minTickGap={30} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: COULEURS.axe, fontSize: 11 }} axisLine={false} tickLine={false} width={40} />
                <Tooltip cursor={{ fill: 'var(--vert-pale)' }}
                  content={<InfoBulle formatLabel={(d) => new Date(d).toLocaleDateString('fr-FR', { dateStyle: 'full' })} formatValeur={(v) => `${formatNombre(v, 1)} kt`} />} />
                {clients.clients.map((c, i) => (
                  <Bar isAnimationActive={false} key={c} dataKey={c} stackId="clients" fill={COULEURS_CLIENTS[c]} name={c}
                    radius={i === clients.clients.length - 1 ? [3, 3, 0, 0] : 0} />
                ))}
              </BarChart>
            </ResponsiveContainer>
            <div className="legende" style={{ marginTop: 12 }}>
              {clients.clients.map(c => (
                <span key={c}><i style={{ background: COULEURS_CLIENTS[c] }} />{c} · <b className="num">{formatNombre(clients.moyennes[c])}</b> t/h moy.</span>
              ))}
            </div>
          </>
        ) : <Squelette hauteur={300} />}
      </Carte>
    </>
  )
}

export default Dashboard
