import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, ReferenceLine } from 'recharts'
import { Target, Sigma, Ruler, TrendingDown, FlaskConical, Fingerprint } from 'lucide-react'
import { api, COULEURS, formatDate, formatNombre, messageErreur } from '../api'
import { Entete, Carte, Kpi, Alerte, Squelette, InfoBulle, Badge } from '../components/ui'

const HORIZONS_TABLEAU = [1, 3, 6, 12, 24]

const veille = (iso) => {
  const d = new Date(iso)
  d.setDate(d.getDate() - 1)
  return d.toISOString().slice(0, 10)
}

function Performances() {
  const [perf, setPerf] = useState(null)
  const [erreur, setErreur] = useState(null)

  useEffect(() => {
    api.get('/performances').then(res => setPerf(res.data)).catch(err => setErreur(messageErreur(err)))
  }, [])

  if (erreur) return <Alerte>{erreur}</Alerte>

  const h6 = perf?.par_horizon.find(h => h.horizon === 6)
  const gain = (h) => Math.round((1 - h.mae / h.mae_persistance) * 100)
  const ent = perf?.entrainement
  const [debutDonnees, finDonnees] = ent ? ent.periode_donnees.split(' -> ') : []
  const couverture = perf?.par_horizon.map(h => ({ horizon: h.horizon, couverture: Math.round(h.couverture_80 * 100) }))

  return (
    <>
      <Entete surtitre="Évaluation" titre="Performances du modèle"
        description={ent ? `Mesurées sur la période de test (à partir du ${formatDate(ent.debut_test)}), jamais vue pendant l'entraînement ni le réglage.` : ''}>
        {ent && <Badge classe="neutre"><FlaskConical size={13} /> Entraîné le {new Date(ent.date).toLocaleDateString('fr-FR')}</Badge>}
      </Entete>

      <div className="grille grille-kpi">
        <Kpi icone={Target} label="R² à 1 h" valeur={perf && formatNombre(perf.r2, 3)} chargement={!perf} detail="Part de la variance expliquée" />
        <Kpi icone={Sigma} label="MAE à 1 h" valeur={perf && formatNombre(perf.mae, 1)} unite="t/h" chargement={!perf} detail="Erreur absolue moyenne" />
        <Kpi icone={Ruler} label="RMSE à 1 h" valeur={perf && formatNombre(perf.rmse, 1)} unite="t/h" chargement={!perf} detail="Pénalise les grosses erreurs" />
        <Kpi icone={TrendingDown} label="Gain vs persistance à 6 h" valeur={h6 && `−${gain(h6)} %`} chargement={!perf}
          detail={perf && `−${gain(perf.par_horizon[0])} % à 1 h · −${gain(perf.par_horizon.find(h => h.horizon === 12))} % à 12 h`} />
      </div>

      <div className="grille grille-2 espace">
        <Carte titre="Erreur selon l'horizon" description="MAE sur le test — plus bas = meilleur"
          action={<div className="legende">
            <span><i style={{ background: COULEURS.modele }} />XGBoost</span>
            <span><i style={{ background: COULEURS.persistance }} />Persistance</span>
            <span><i style={{ background: COULEURS.moyenne }} />Moyenne</span>
          </div>}>
          {perf ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={perf.par_horizon} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid stroke={COULEURS.grille} vertical={false} />
                <XAxis dataKey="horizon" tickFormatter={(h) => `${h}h`} tick={{ fill: COULEURS.axe, fontSize: 11 }} axisLine={false} tickLine={false} interval={2} />
                <YAxis domain={[0, 'auto']} tick={{ fill: COULEURS.axe, fontSize: 11 }} axisLine={false} tickLine={false} width={40} />
                <Tooltip content={<InfoBulle formatLabel={(h) => `Horizon ${h} h`} formatValeur={(v) => `${formatNombre(v, 1)} t/h`} />} />
                <Line isAnimationActive={false} type="monotone" dataKey="mae_persistance" stroke={COULEURS.persistance} strokeWidth={2} strokeDasharray="6 4" dot={false} name="Persistance" />
                <Line isAnimationActive={false} type="monotone" dataKey="mae_moyenne" stroke={COULEURS.moyenne} strokeWidth={2} strokeDasharray="2 4" dot={false} name="Moyenne" />
                <Line isAnimationActive={false} type="monotone" dataKey="mae" stroke={COULEURS.modele} strokeWidth={3} dot={{ r: 2.5 }} name="XGBoost" />
              </LineChart>
            </ResponsiveContainer>
          ) : <Squelette hauteur={300} />}
        </Carte>

        <Carte titre="Fiabilité de la fourchette" description="Part des heures de test où la valeur réelle tombe dans l'intervalle annoncé — ligne orange : cible de 80 %">
          {perf ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={couverture} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid stroke={COULEURS.grille} vertical={false} />
                <XAxis dataKey="horizon" tickFormatter={(h) => `${h}h`} tick={{ fill: COULEURS.axe, fontSize: 11 }} axisLine={false} tickLine={false} interval={2} />
                <YAxis domain={[50, 100]} tick={{ fill: COULEURS.axe, fontSize: 11 }} axisLine={false} tickLine={false} width={40} tickFormatter={(v) => `${v}%`} />
                <Tooltip cursor={{ fill: 'var(--vert-pale)' }} content={<InfoBulle formatLabel={(h) => `Horizon ${h} h`} formatValeur={(v) => `${v} %`} />} />
                <ReferenceLine y={80} stroke={COULEURS.persistance} strokeDasharray="4 4" />
                <Bar isAnimationActive={false} dataKey="couverture" fill={COULEURS.modele} radius={[4, 4, 0, 0]} name="Couverture" />
              </BarChart>
            </ResponsiveContainer>
          ) : <Squelette hauteur={300} />}
        </Carte>
      </div>

      <Carte className="espace" titre="Comparaison aux modèles de référence" description="Erreur absolue moyenne (t/h) sur le test. Un modèle n'est utile que s'il bat ces références simples.">
        {perf ? (
          <div className="tableau-conteneur">
            <table className="tableau">
              <thead>
                <tr>
                  {['Horizon', 'XGBoost', 'Persistance', 'Même heure J-1', 'Moyenne', 'Gain', 'R²', 'Couverture 80 %'].map(t => <th key={t}>{t}</th>)}
                </tr>
              </thead>
              <tbody>
                {perf.par_horizon.filter(h => HORIZONS_TABLEAU.includes(h.horizon)).map(row => (
                  <tr key={row.horizon}>
                    <td><b>{row.horizon} h</b></td>
                    <td className="meilleur">{formatNombre(row.mae, 1)}</td>
                    <td>{formatNombre(row.mae_persistance, 1)}</td>
                    <td>{formatNombre(row.mae_meme_heure, 1)}</td>
                    <td>{formatNombre(row.mae_moyenne, 1)}</td>
                    <td><Badge>−{gain(row)} %</Badge></td>
                    <td>{formatNombre(row.r2, 3)}</td>
                    <td>{Math.round(row.couverture_80 * 100)} %</td>
                  </tr>
                ))}
                <tr>
                  <td><b>&gt; 24 h</b> <span style={{ color: 'var(--texte-3)', fontSize: '0.8rem' }}>long terme</span></td>
                  <td className="meilleur">{formatNombre(perf.long_terme.mae, 1)}</td>
                  <td>—</td>
                  <td>—</td>
                  <td>{formatNombre(perf.long_terme.mae_moyenne, 1)}</td>
                  <td><Badge classe="neutre">−{Math.round((1 - perf.long_terme.mae / perf.long_terme.mae_moyenne) * 100)} % vs moy.</Badge></td>
                  <td>{formatNombre(perf.long_terme.r2, 3)}</td>
                  <td>{Math.round(perf.long_terme.couverture_80 * 100)} %</td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : <Squelette hauteur={260} />}
      </Carte>

      {ent && (
        <div className="grille grille-2">
          <Carte titre="Validation chronologique" description="Les données futures ne servent jamais à entraîner le modèle">
            <div style={{ display: 'flex', height: 12, borderRadius: 6, overflow: 'hidden', marginBottom: 18 }}>
              <div style={{ flex: 5, background: COULEURS.modele }} />
              <div style={{ flex: 1, background: COULEURS.moyenne }} />
              <div style={{ flex: 2, background: COULEURS.persistance }} />
            </div>
            {[
              { role: 'Entraînement', periode: `${debutDonnees} → ${veille(ent.debut_validation)}`, couleur: COULEURS.modele, texte: 'Apprentissage des modèles' },
              { role: 'Validation', periode: `${ent.debut_validation} → ${veille(ent.debut_test)}`, couleur: COULEURS.moyenne, texte: "Nombre d'arbres, calibration des fourchettes" },
              { role: 'Test', periode: `${ent.debut_test} → ${finDonnees}`, couleur: COULEURS.persistance, texte: 'Évaluation finale, données jamais vues' },
            ].map(p => (
              <div key={p.role} className="ligne-info">
                <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <i style={{ width: 10, height: 10, borderRadius: 3, background: p.couleur, display: 'inline-block' }} />
                  <span><b style={{ color: 'var(--texte)' }}>{p.role}</b><br /><span style={{ fontSize: '0.8rem' }}>{p.texte}</span></span>
                </span>
                <span className="num">{p.periode}</span>
              </div>
            ))}
          </Carte>

          <Carte titre="Reproductibilité" description="Deux entraînements successifs produisent des modèles identiques"
            action={<span className="kpi-icone"><Fingerprint size={18} /></span>}>
            {[
              ['Dernier entraînement', new Date(ent.date).toLocaleString('fr-FR')],
              ['Graine aléatoire', ent.graine],
              ['Python · XGBoost · pandas', `${ent.versions.python} · ${ent.versions.xgboost} · ${ent.versions.pandas}`],
              ...Object.entries(ent.empreinte_donnees).map(([f, h]) => [f, <code key={f} style={{ fontSize: '0.8rem' }}>{h}</code>]),
            ].map(([k, v]) => (
              <div key={k} className="ligne-info">
                <span>{k}</span>
                <span style={{ wordBreak: 'break-all' }}>{v}</span>
              </div>
            ))}
          </Carte>
        </div>
      )}
    </>
  )
}

export default Performances
