import { Home, LayoutDashboard, LineChart, Gauge, ClipboardCheck } from 'lucide-react'

export const LIENS = [
  { path: '/', label: 'Accueil', desc: "Vue d'ensemble", icone: Home },
  { path: '/dashboard', label: 'Dashboard', desc: 'Analyse des données', icone: LayoutDashboard },
  { path: '/prediction', label: 'Prédiction', desc: "Jusqu'à fin 2026", icone: LineChart },
  { path: '/performances', label: 'Performances', desc: 'Évaluation du modèle', icone: Gauge },
  { path: '/qualite', label: 'Qualité des données', desc: 'Audit avant / après', icone: ClipboardCheck },
]
