import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ComposedChart, Area, Bar, Cell, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { CalendarClock, Sparkles, Loader2, LineChart as IconeCourbe } from 'lucide-react'
import { api, ajouterHeures, COULEURS, FIABILITES, STATUTS, formatDateHeure, formatNombre, messageErreur } from '../api'
import { Entete, Carte, Badge, Alerte } from '../components/ui'

const p2 = (n) => String(n).padStart(2, '0')
const versChamp = (d) => `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())}T${p2(d.getHours())}:00`

const RACCOURCIS = [
  { label: '+1 h', cible: (derniere) => ajouterHeures(derniere, 1) },
  { label: '+6 h', cible: (derniere) => ajouterHeures(derniere, 6) },
  { label: '+24 h', cible: (derniere) => ajouterHeures(derniere, 24) },
  { label: '+7 jours', cible: (derniere) => ajouterHeures(derniere, 24 * 7) },
  { label: '+1 an', cible: (derniere) => ajouterHeures(derniere, 24 * 365) },
  { label: "Aujourd'hui", cible: () => versChamp(new Date()), enAvant: true },
  { label: '31 déc. 2026', cible: () => '2026-12-31T12:00', enAvant: true },
]

const ECHELLE_MAX = 2800

function Prediction() {
  const [searchParams] = useSearchParams()
  const [derniere, setDerniere] = useState(null)
  const [moyenne, setMoyenne] = useState(null)
  const [dateHeure, setDateHeure] = useState('')
  const [raccourci, setRaccourci] = useState(null)
  const [resultat, setResultat] = useState(null)
  const [chargement, setChargement] = useState(false)
  const [erreur, setErreur] = useState(null)

  const predire = async (cible) => {
    if (!cible) {
      setErreur('Sélectionnez une date et une heure')
      return
    }
    setChargement(true)
    setErreur(null)
    try {
      const res = await api.get('/predict-future', { params: { target_datetime: cible } })
      setResultat(res.data)
    } catch (err) {
      setErreur(messageErreur(err))
      setResultat(null)
    }
    setChargement(false)
  }

  useEffect(() => {
    api.get('/stats')
      .then(res => {
        setDerniere(res.data.derniere_date)
        setMoyenne(res.data.debit_moyen)
        // Lien direct vers une date : /prediction?date=2026-10-29T10:00
        const date = searchParams.get('date')
        if (date) {
          setDateHeure(date)
          predire(date)
        }
      })
      .catch(err => setErreur(messageErreur(err)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const choisirRaccourci = (r) => {
    const cible = r.cible(derniere)
    setRaccourci(r.label)
    setDateHeure(cible)
    predire(cible)
  }

  const statut = resultat && STATUTS[resultat.statut]
  const fiabilite = resultat?.fiabilite && FIABILITES[resultat.fiabilite]
  const pourcent = (v) => `${Math.max(0, Math.min(100, (v / ECHELLE_MAX) * 100))}%`
  const journalier = resultat?.pas_serie === 'jour' || resultat?.pas_serie === 'semaine'
  const DESCRIPTIONS_SERIE = {
    heure: "Prévision heure par heure jusqu'à la date cible",
    jour: "Moyenne journalière, de la dernière mesure jusqu'à la date cible",
    semaine: "Moyenne hebdomadaire, de la dernière mesure jusqu'à la date cible",
  }

  return (
    <>
      <Entete surtitre="Prévision" titre="Prédiction du débit"
        description="Choisissez une date jusqu'au 31 décembre 2026. Le modèle adapté à l'horizon est sélectionné automatiquement." />

      <div className="grille grille-prediction espace">
        <Carte titre="Paramètres" description={derniere ? `Dernière mesure : ${formatDateHeure(derniere)}` : 'Chargement…'}>
          <div className="champ" style={{ marginBottom: 18 }}>
            <label htmlFor="date-cible">Date et heure cible</label>
            <input id="date-cible" type="datetime-local" value={dateHeure} step={3600}
              min={derniere ? ajouterHeures(derniere, 1) : undefined}
              max={derniere ? ajouterHeures(derniere, 24 * 731) : undefined}
              onChange={(e) => { setDateHeure(e.target.value); setRaccourci(null) }} />
            <div className="aide">Horizon maximal : 31 décembre 2026</div>
          </div>

          <div className="champ" style={{ marginBottom: 20 }}>
            <label>Raccourcis</label>
            <div className="puces">
              {RACCOURCIS.map(r => (
                <button key={r.label} className={`puce ${raccourci === r.label ? 'actif' : ''}`}
                  style={r.enAvant && raccourci !== r.label ? { borderColor: 'var(--vert)', color: 'var(--vert)' } : undefined}
                  disabled={!derniere} onClick={() => choisirRaccourci(r)}>
                  {r.label}
                </button>
              ))}
            </div>
          </div>

          <button className="bouton plein" onClick={() => predire(dateHeure)} disabled={chargement}>
            {chargement ? <><Loader2 size={18} className="tourne" /> Calcul en cours…</> : <><Sparkles size={18} /> Prédire le débit</>}
          </button>

          {erreur && <div style={{ marginTop: 14 }}><Alerte>{erreur}</Alerte></div>}

          <div style={{ marginTop: 22 }}>
            {Object.entries(FIABILITES).map(([cle, f], i) => (
              <div key={cle} className="ligne-info" style={{ borderTop: i === 0 ? 'none' : undefined }}>
                <span><Badge classe={f.classe}>{f.label}</Badge></span>
                <span style={{ fontWeight: 500, color: 'var(--texte-2)' }}>{['1 – 12 h', '12 – 24 h', '24 h – fin 2026'][i]}</span>
              </div>
            ))}
          </div>
        </Carte>

        <Carte titre="Résultat">
          {resultat ? (
            <div className="apparition">
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 18 }}>
                {statut && <Badge classe={statut.classe} point>{statut.label}</Badge>}
                {fiabilite && <Badge classe={fiabilite.classe}>{fiabilite.label}</Badge>}
                {resultat.source === 'historique_reel' && <Badge classe="neutre">Valeur mesurée</Badge>}
              </div>

              <div style={{ color: 'var(--texte-2)', fontWeight: 500 }}>Débit prévu le {formatDateHeure(dateHeure)}</div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginTop: 6 }}>
                <span className="resultat-valeur" style={{ color: 'var(--vert)' }}>{formatNombre(resultat.debit_predit)}</span>
                <span style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--texte-3)' }}>t/h</span>
              </div>

              {resultat.intervalle_bas !== undefined && (
                <>
                  <div className="jauge">
                    <div className="jauge-plage" style={{ left: pourcent(resultat.intervalle_bas), right: `calc(100% - ${pourcent(resultat.intervalle_haut)})` }} />
                    <div className="jauge-marqueur" style={{ left: pourcent(resultat.debit_predit) }} />
                  </div>
                  <div className="jauge-legende"><span>0</span><span>{formatNombre(ECHELLE_MAX)} t/h</span></div>
                </>
              )}

              <div style={{ marginTop: 18 }}>
                {resultat.intervalle_bas !== undefined && (
                  <div className="ligne-info">
                    <span>Fourchette probable (80 %)</span>
                    <span className="num">{formatNombre(resultat.intervalle_bas)} – {formatNombre(resultat.intervalle_haut)} t/h</span>
                  </div>
                )}
                <div className="ligne-info">
                  <span>Horizon</span>
                  <span className="num">
                    {resultat.hours_ahead} h{resultat.hours_ahead >= 48 && ` (${formatNombre(resultat.hours_ahead / 24)} jours)`}
                  </span>
                </div>
                {resultat.volume_jour_kt !== undefined && (
                  <div className="ligne-info">
                    <span>Volume prévu sur la journée</span>
                    <span className="num">{formatNombre(resultat.volume_jour_kt, 1)} kt</span>
                  </div>
                )}
                {moyenne && (
                  <div className="ligne-info">
                    <span>Écart à la moyenne historique</span>
                    <span className="num">{resultat.debit_predit >= moyenne ? '+' : ''}{formatNombre(((resultat.debit_predit - moyenne) / moyenne) * 100, 1)} %</span>
                  </div>
                )}
              </div>

              {fiabilite && <div style={{ marginTop: 14 }}><Alerte info>{fiabilite.texte}</Alerte></div>}
            </div>
          ) : (
            <div className="vide">
              <div className="vide-icone"><CalendarClock size={26} /></div>
              <div style={{ fontWeight: 600, color: 'var(--texte-2)' }}>Aucune prédiction pour l'instant</div>
              <div style={{ maxWidth: 320 }}>Choisissez une date ou un raccourci pour obtenir le débit prévu et sa fourchette.</div>
            </div>
          )}
        </Carte>
      </div>

      {resultat?.profil_jour?.length > 0 && (
        <Carte className="espace" titre={`Profil de la journée du ${new Date(dateHeure).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}`}
          description={`Débit prévu heure par heure · volume total ${formatNombre(resultat.volume_jour_kt, 1)} kt · heure choisie en surbrillance`}
          action={<div className="legende">
            <span><i style={{ background: COULEURS.modele }} />Heure choisie</span>
            <span><i style={{ background: '#9fd3b4' }} />Autres heures</span>
            <span><i style={{ background: 'rgba(0,132,61,0.2)' }} />Fourchette 80 %</span>
          </div>}>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={resultat.profil_jour} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={COULEURS.grille} vertical={false} />
              <XAxis dataKey="heure" tickFormatter={(h) => `${h}h`} tick={{ fill: COULEURS.axe, fontSize: 11 }} interval={1} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: COULEURS.axe, fontSize: 11 }} axisLine={false} tickLine={false} width={50} domain={[0, 'auto']} tickFormatter={(v) => formatNombre(v)} />
              <Tooltip cursor={{ fill: 'var(--vert-pale)' }} content={({ active, payload }) => {
                if (!active || !payload?.length) return null
                const p = payload[0].payload
                return (
                  <div className="tooltip">
                    <div className="tooltip-titre">{p.heure}h – {p.heure + 1}h</div>
                    <div className="tooltip-ligne">Débit prévu <b>{formatNombre(p.debit)} t/h</b></div>
                    <div className="tooltip-ligne">Fourchette <b>{formatNombre(p.bas)} – {formatNombre(p.haut)}</b></div>
                  </div>
                )
              }} />
              <Area isAnimationActive={false} type="monotone" dataKey={(d) => [d.bas, d.haut]} stroke="none" fill={COULEURS.modele} fillOpacity={0.12} />
              <Bar isAnimationActive={false} dataKey="debit" radius={[4, 4, 0, 0]} barSize={18}>
                {resultat.profil_jour.map(p => (
                  <Cell key={p.heure} fill={p.heure === new Date(dateHeure).getHours() ? COULEURS.modele : '#9fd3b4'} />
                ))}
              </Bar>
              {moyenne && <ReferenceLine y={moyenne} stroke={COULEURS.moyenne} strokeDasharray="4 4" />}
            </ComposedChart>
          </ResponsiveContainer>
        </Carte>
      )}

      {resultat?.serie?.length > 0 && (
        <Carte titre="Évolution prévue" description={DESCRIPTIONS_SERIE[resultat.pas_serie]}
          action={<div className="legende">
            <span><i style={{ background: COULEURS.modele }} />Débit prévu</span>
            <span><i style={{ background: 'rgba(0,132,61,0.2)' }} />Fourchette 80 %</span>
            <span><i style={{ background: COULEURS.moyenne }} />Moyenne historique</span>
          </div>}>
          <ResponsiveContainer width="100%" height={340}>
            <ComposedChart data={resultat.serie} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={COULEURS.grille} vertical={false} />
              <XAxis dataKey="date" tick={{ fill: COULEURS.axe, fontSize: 11 }} minTickGap={50} axisLine={false} tickLine={false}
                tickFormatter={(d) => journalier ? new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }) : d.slice(11, 16)} />
              <YAxis tick={{ fill: COULEURS.axe, fontSize: 11 }} axisLine={false} tickLine={false} width={50} domain={['auto', 'auto']} tickFormatter={(v) => formatNombre(v)} />
              <Tooltip content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null
                const p = payload[0].payload
                return (
                  <div className="tooltip">
                    <div className="tooltip-titre">{resultat.pas_serie === 'semaine' ? `Semaine du ${new Date(label).toLocaleDateString('fr-FR', { dateStyle: 'long' })}` : journalier ? new Date(label).toLocaleDateString('fr-FR', { dateStyle: 'full' }) : label}</div>
                    <div className="tooltip-ligne">Débit prévu <b>{formatNombre(p.debit)} t/h</b></div>
                    <div className="tooltip-ligne">Fourchette <b>{formatNombre(p.bas)} – {formatNombre(p.haut)}</b></div>
                  </div>
                )
              }} />
              {moyenne && <ReferenceLine y={moyenne} stroke={COULEURS.moyenne} strokeDasharray="4 4" />}
              <Area isAnimationActive={false} dataKey={(d) => [d.bas, d.haut]} stroke="none" fill={COULEURS.modele} fillOpacity={0.15} name="Fourchette" />
              <Line isAnimationActive={false} type="monotone" dataKey="debit" stroke={COULEURS.modele} strokeWidth={2.5} dot={false} name="Débit prévu" />
            </ComposedChart>
          </ResponsiveContainer>
        </Carte>
      )}

      {!resultat && (
        <Carte>
          <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
            <div className="vide-icone" style={{ flexShrink: 0 }}><IconeCourbe size={22} /></div>
            <div style={{ color: 'var(--texte-2)' }}>
              La courbe de prévision et sa fourchette d'incertitude s'afficheront ici, heure par heure jusqu'à 3 jours,
              puis en moyenne journalière pour les horizons plus lointains.
            </div>
          </div>
        </Carte>
      )}
    </>
  )
}

export default Prediction
