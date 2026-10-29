import { useEffect, useState } from 'react'
import { Copy, PlugZap, CalendarX, EyeOff, Rows3, CalendarRange, CheckCircle2, XCircle } from 'lucide-react'
import { api, formatNombre, messageErreur } from '../api'
import { Entete, Carte, Kpi, Alerte, Badge, Squelette } from '../components/ui'

function Probleme({ icone: Icone, titre, constat, correction, chiffre }) {
  return (
    <div className="probleme">
      <div className="probleme-icone"><Icone size={18} /></div>
      <div className="probleme-corps">
        <div className="probleme-titre">
          <h4>{titre}</h4>
          <Badge><CheckCircle2 size={13} /> Corrigé</Badge>
        </div>
        <div className="probleme-colonnes">
          <div>
            <div className="probleme-label avant">Constat</div>
            <p>{constat}</p>
          </div>
          <div>
            <div className="probleme-label apres">Correction</div>
            <p>{correction}</p>
          </div>
        </div>
      </div>
      {chiffre && <div className="probleme-chiffre num">{chiffre}</div>}
    </div>
  )
}

function Qualite() {
  const [q, setQ] = useState(null)
  const [perf, setPerf] = useState(null)
  const [erreur, setErreur] = useState(null)

  useEffect(() => {
    api.get('/qualite-donnees').then(res => setQ(res.data)).catch(err => setErreur(messageErreur(err)))
    api.get('/performances').then(res => setPerf(res.data)).catch(() => {})
  }, [])

  if (erreur) return <Alerte>{erreur}</Alerte>

  const b = q?.brut
  const a = q?.ancien_pipeline
  const n = q?.nouveau_modele
  const ecart = (mae, ref) => ((mae - ref) / ref) * 100
  const h6 = perf?.par_horizon.find(h => h.horizon === 6)

  return (
    <>
      <Entete surtitre="Audit" titre="Qualité des données"
        description="Problèmes détectés dans les données et dans l'ancien pipeline, et corrections appliquées. Tous les chiffres sont recalculés à chaque entraînement à partir des fichiers bruts." />

      <div className="grille grille-kpi">
        <Kpi icone={Copy} label="Heures en double supprimées" valeur={b && formatNombre(b.doublons)} chargement={!q}
          detail="Chevauchement des fichiers mensuels" />
        <Kpi icone={PlugZap} label="Heures JFT complétées" valeur={b && formatNombre(b.jft_absent_heures)} chargement={!q}
          detail={b && `${b.jft_absent_periode} · ≈ ${formatNombre(b.jft_moyen)} t/h`} />
        <Kpi icone={CalendarX} label="Heures récupérées" valeur={a && formatNombre(a.heures_perdues)} chargement={!q}
          detail="Absentes de l'ancien dataset" />
        <Kpi icone={EyeOff} label="Fuite de données corrigée" valeur={a && `${Math.round(a.part_vente_jour_meme * 100)} %`} chargement={!q}
          detail="des heures utilisaient les ventes du jour même" />
      </div>

      <Carte className="espace" titre="Problèmes détectés et corrections" description="Du fichier brut à la série horaire utilisée par les modèles">
        {q ? (
          <div className="problemes">
            <Probleme icone={Copy} titre="Heures en double"
              constat={`${b.doublons} heures apparaissent deux fois dans le fichier brut (début de chaque mois), ${a ? `${a.doublons} dans l'ancien dataset ML` : ''}. Les lags « 1 h avant » pointaient alors sur la même heure.`}
              correction="Suppression des doublons (lignes strictement identiques), puis vérification automatique de l'unicité des horodatages."
              chiffre={`−${b.doublons} h`} />
            <Probleme icone={PlugZap} titre="Cible incohérente : JFT manquant"
              constat={a
                ? `L'ancien débit total n'incluait jamais JFT (écart médian ${formatNombre(a.ecart_median_cible_sans_jft, 1)} t/h avec la somme des clients sans JFT, ${formatNombre(a.ecart_median_cible_avec_jft)} t/h avec). L'ancien script l'ajoutait seulement en mai : la feuille « Juin » de l'extraction JFT n'était pas lue.`
                : `JFT est absent du fichier principal du ${b.jft_absent_periode}.`}
              correction={`Débit total = somme des 7 clients sur toute la période. JFT de mai–juin complété par l'extraction (les deux feuilles sont lues).`}
              chiffre={`+${formatNombre(b.jft_moyen)} t/h`} />
            {a && (
              <Probleme icone={CalendarRange} titre="Données perdues"
                constat={`${a.heures_perdues} heures valides du fichier brut manquaient dans l'ancien dataset, dont un trou de ${formatNombre(a.plus_long_trou.jours)} jours (${a.plus_long_trou.debut} → ${a.plus_long_trou.fin}).`}
                correction="Reconstruction complète depuis le fichier brut, sans passer par le dataset intermédiaire."
                chiffre={`+${a.heures_perdues} h`} />
            )}
            <Probleme icone={Rows3} titre="Pas de temps irrégulier"
              constat={`${b.heures_manquantes} heures manquantes dans le brut. Les lags étaient calculés « ligne par ligne » : à travers un trou, « 1 h avant » pouvait valoir plusieurs jours.`}
              correction={`Index horaire régulier. ${b.heures_interpolees} heures interpolées (trous ≤ 3 h), ${b.heures_vides} heures laissées vides (trous plus longs, jamais inventées).`}
              chiffre={`${b.heures_interpolees} h`} />
            {a && (
              <Probleme icone={EyeOff} titre="Fuite de données (data leakage)"
                constat={`« Vente/heure » valait les ventes réalisées du jour même ÷ 24 pour ${Math.round(a.part_vente_jour_meme * 100)} % des heures : une information connue seulement en fin de journée, indisponible au moment de prévoir.`}
                correction="Remplacée par les ventes de la veille (J-1). Un test automatique vérifie qu'aucune variable ne dépend du futur."
                chiffre="J-1" />
            )}
            {a && (
              <Probleme icone={CalendarX} titre="Variable « Mois » non généralisable"
                constat={`« Mois » était la ${a.rang_variable_mois}e variable la plus importante de l'ancien modèle, alors que les mois du test n'apparaissent jamais dans l'entraînement.`}
                correction="Mois et jour du mois retirés : seuls l'heure, le jour de la semaine et les jours fériés sont utilisés."
                chiffre={`#${a.rang_variable_mois}`} />
            )}
          </div>
        ) : <Squelette hauteur={420} />}
      </Carte>

      {a && n && (
        <Carte titre="Ancien modèle vs nouveau modèle" description="Les cibles diffèrent (JFT inclus dans la nouvelle) : chaque modèle est comparé à sa propre persistance, sur sa propre période de test.">
          <div className="tableau-conteneur">
            <table className="tableau">
              <thead>
                <tr>
                  <th>Modèle</th>
                  <th>Résultat annoncé</th>
                  <th>MAE mesurée (1 h)</th>
                  <th>MAE persistance</th>
                  <th>Écart vs persistance</th>
                  <th>Verdict</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><b>Ancien XGBoost v3</b><br /><span style={{ color: 'var(--texte-3)', fontSize: '0.8rem' }}>test {a.periode_test}</span></td>
                  <td>R² {a.r2_annonce} · MAE {a.mae_annoncee} t/h</td>
                  <td className="num">{formatNombre(a.mae_ancien_modele, 1)} t/h</td>
                  <td className="num">{formatNombre(a.mae_persistance, 1)} t/h</td>
                  <td className="num" style={{ color: 'var(--rouge)', fontWeight: 700 }}>
                    {ecart(a.mae_ancien_modele, a.mae_persistance) > 0 ? '+' : ''}{formatNombre(ecart(a.mae_ancien_modele, a.mae_persistance), 1)} %
                  </td>
                  <td><Badge classe="rouge"><XCircle size={13} /> Pas mieux que « rien ne change »</Badge></td>
                </tr>
                <tr>
                  <td><b>Nouveau pipeline</b><br /><span style={{ color: 'var(--texte-3)', fontSize: '0.8rem' }}>test nov. – déc. 2024</span></td>
                  <td>—</td>
                  <td className="num">{formatNombre(n.mae, 1)} t/h</td>
                  <td className="num">{formatNombre(n.mae_persistance, 1)} t/h</td>
                  <td className="num" style={{ color: 'var(--vert)', fontWeight: 700 }}>{formatNombre(ecart(n.mae, n.mae_persistance), 1)} %</td>
                  <td><Badge><CheckCircle2 size={13} /> Meilleur à tous les horizons{h6 ? ` (${formatNombre(ecart(h6.mae, h6.mae_persistance), 0)} % à 6 h)` : ''}</Badge></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: 14 }}>
            <Alerte info>
              Les chiffres annoncés pour l'ancien modèle (R² {a.r2_annonce}, MAE {a.mae_annoncee} t/h) ne sont pas reproductibles : réévalué sur ses propres données,
              il fait légèrement moins bien que la persistance. Le nouveau pipeline est évalué sans fuite, sur une période jamais vue, et reproduit les mêmes résultats à chaque entraînement.
            </Alerte>
          </div>
        </Carte>
      )}
    </>
  )
}

export default Qualite
