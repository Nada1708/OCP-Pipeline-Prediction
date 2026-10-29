import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Activity, Clock, Gauge, AlertOctagon, ArrowRight, Database, Layers, Cpu, LineChart } from 'lucide-react'
import { api, ajouterHeures, formatNombre, messageErreur } from '../api'
import { Carte, Kpi, Alerte, Badge, InfoBulle } from '../components/ui'

const ETAPES = [
  { icone: Database, titre: 'Données nettoyées', texte: 'Relevés horaires des 7 clients, doublons supprimés, JFT intégré sur toute la période.' },
  { icone: Layers, titre: 'Variables sans fuite', texte: "Uniquement l'information disponible à l'instant de la prévision : historique, état des clients, calendrier." },
  { icone: Cpu, titre: 'Modèles par horizon', texte: 'Un modèle XGBoost par horizon de 1 à 24 h, puis un profil calendaire jusqu\'à fin 2026.' },
  { icone: LineChart, titre: 'Prévision + fourchette', texte: 'Chaque prévision est accompagnée d\'un intervalle à 80 % vérifié sur des données jamais vues.' },
]

function Accueil() {
  const [stats, setStats] = useState(null)
  const [perf, setPerf] = useState(null)
  const [prochaines, setProchaines] = useState(null)
  const [erreur, setErreur] = useState(null)

  useEffect(() => {
    api.get('/stats')
      .then(res => {
        setStats(res.data)
        return api.get('/predict-future', { params: { target_datetime: ajouterHeures(res.data.derniere_date, 24) } })
      })
      .then(res => setProchaines(res.data.serie.map(p => ({ ...p, heure: p.date.slice(11, 16) }))))
      .catch(err => setErreur(messageErreur(err)))
    api.get('/performances').then(res => setPerf(res.data)).catch(() => {})
  }, [])

  const gain6 = perf && (() => {
    const h6 = perf.par_horizon.find(h => h.horizon === 6)
    return Math.round((1 - h6.mae / h6.mae_persistance) * 100)
  })()

  return (
    <>
      <section className="hero apparition">
        <div className="hero-grille">
          <div>
            <Badge classe="neutre" point pulse>Modèle actif</Badge>
            <h1 style={{ marginTop: 16 }}>Prévision du débit horaire du pipeline</h1>
            <p>
              Anticiper le débit à envoyer de Khouribga vers les clients de Jorf Lasfar,
              de l'heure suivante jusqu'à fin 2026, avec une fourchette d'incertitude fiable.
            </p>
            <div className="hero-chiffres">
              <div><strong>{perf ? formatNombre(perf.r2, 2) : '—'}</strong><span>R² à 1 h</span></div>
              <div><strong>{perf ? `−${gain6} %` : '—'}</strong><span>d'erreur vs persistance à 6 h</span></div>
              <div><strong>{stats ? formatNombre(stats.nb_lignes) : '—'}</strong><span>heures de données</span></div>
            </div>
            <div style={{ display: 'flex', gap: 10, marginTop: 26, flexWrap: 'wrap' }}>
              <Link to="/prediction" className="bouton" style={{ background: 'white', color: 'var(--vert-fonce)', textDecoration: 'none' }}>
                Lancer une prédiction <ArrowRight size={16} />
              </Link>
              <Link to="/performances" className="bouton" style={{ background: 'rgba(255,255,255,0.12)', textDecoration: 'none' }}>
                Voir l'évaluation
              </Link>
            </div>
          </div>

          <div className="hero-panneau">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div>
                <div style={{ fontWeight: 700 }}>Prochaines 24 heures</div>
                <div style={{ fontSize: '0.8rem', opacity: 0.75 }}>Prévision et fourchette à 80 %</div>
              </div>
              {prochaines && (
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800 }} className="num">
                    {formatNombre(prochaines.reduce((s, p) => s + p.debit, 0) / prochaines.length)}
                  </div>
                  <div style={{ fontSize: '0.75rem', opacity: 0.75 }}>t/h en moyenne</div>
                </div>
              )}
            </div>
            {erreur ? (
              <div style={{ fontSize: '0.85rem', opacity: 0.9 }}>{erreur}</div>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={prochaines ?? []} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="degradeHero" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ffffff" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#ffffff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="heure" tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 11 }} axisLine={false} tickLine={false} interval={5} />
                  <YAxis tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 11 }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
                  <Tooltip content={<InfoBulle formatValeur={(v) => Array.isArray(v) ? v.map(x => formatNombre(x)).join(' – ') + ' t/h' : `${formatNombre(v)} t/h`} />} />
                  <Area isAnimationActive={false} dataKey={(d) => [d.bas, d.haut]} stroke="none" fill="#ffffff" fillOpacity={0.15} name="Fourchette" />
                  <Area isAnimationActive={false} type="monotone" dataKey="debit" stroke="#ffffff" strokeWidth={2.5} fill="url(#degradeHero)" name="Débit prévu" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </section>

      {erreur && <div className="espace"><Alerte>{erreur}</Alerte></div>}

      <div className="grille grille-kpi">
        <Kpi icone={Activity} label="Dernier débit mesuré" valeur={formatNombre(stats?.dernier_debit)} unite="t/h" chargement={!stats}
          detail={stats && new Date(stats.derniere_date).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })} />
        <Kpi icone={Clock} label="Moyenne des 24 dernières heures" valeur={formatNombre(stats?.moyenne_24h)} unite="t/h" chargement={!stats}
          detail={stats && `${stats.moyenne_24h >= stats.debit_moyen ? 'Au-dessus' : 'En dessous'} de la moyenne historique`} />
        <Kpi icone={Gauge} label="Débit moyen historique" valeur={formatNombre(stats?.debit_moyen)} unite="t/h" chargement={!stats}
          detail={stats?.periode} />
        <Kpi icone={AlertOctagon} label="Heures d'arrêt (30 derniers jours)" valeur={stats?.arrets_30j} unite="h" chargement={!stats}
          detail="Débit inférieur à 500 t/h" />
      </div>

      <Carte titre="Comment fonctionne la prévision" description="Un pipeline reproductible, de la donnée brute à la prévision servie par l'API">
        <div className="grille grille-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))' }}>
          {ETAPES.map(({ icone: Icone, titre, texte }, i) => (
            <div key={titre} className="etape">
              <div className="etape-numero"><Icone size={17} /></div>
              <div>
                <h4><span style={{ color: 'var(--texte-3)', marginRight: 6 }}>0{i + 1}</span>{titre}</h4>
                <p>{texte}</p>
              </div>
            </div>
          ))}
        </div>
      </Carte>
    </>
  )
}

export default Accueil
