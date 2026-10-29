import axios from 'axios'

export const api = axios.create({ baseURL: 'http://127.0.0.1:8000' })

export const messageErreur = (err) =>
  err.response?.data?.detail || "Impossible de joindre l'API. Vérifiez que le backend est lancé sur le port 8000."

export const COULEURS = {
  modele: '#00843d',
  persistance: '#d97706',
  moyenne: '#2563eb',
  grille: '#e3e8e5',
  axe: '#85948c',
}

export const COULEURS_CLIENTS = {
  IMACID: '#00843d',
  JFO: '#2563eb',
  JFD: '#d97706',
  JFT: '#7c3aed',
  JFQ: '#0891b2',
  JFF: '#db2777',
  PMP: '#65a30d',
}

export const formatNombre = (v, decimales = 0) =>
  v === null || v === undefined ? '—' : Number(v).toLocaleString('fr-FR', { maximumFractionDigits: decimales, minimumFractionDigits: decimales })

export const formatDateHeure = (iso) =>
  new Date(iso).toLocaleString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })

export const formatDate = (iso) =>
  new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })

// Dates de l'API sans fuseau : manipulees en heure locale, au format attendu par /predict-future
export const ajouterHeures = (iso, heures) => {
  const d = new Date(iso)
  d.setHours(d.getHours() + heures)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:00`
}

export const STATUTS = {
  eleve: { label: 'Débit élevé', classe: '', texte: 'Production optimale' },
  normal: { label: 'Débit normal', classe: 'bleu', texte: 'Production standard' },
  faible: { label: 'Débit faible', classe: 'ambre', texte: 'Vérifier le pipeline' },
}

export const FIABILITES = {
  court_terme: { label: 'Court terme', classe: '', texte: 'Basée sur les dernières mesures de chaque client : la prévision la plus précise.' },
  transition: { label: 'Moyen terme', classe: 'bleu', texte: 'Transition entre les dernières mesures et le profil horaire habituel.' },
  long_terme: { label: 'Long terme', classe: 'ambre', texte: "Profil habituel selon l'heure, le jour et les jours fériés. Les arrêts ne sont pas prévisibles à cet horizon." },
}
