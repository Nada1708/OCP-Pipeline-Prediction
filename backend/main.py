import json
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# Le pipeline (donnees, variables, modeles) est partage avec train.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ocp_ml.config import CIBLE, REPORTS_DIR, SEUIL_ARRET
from ocp_ml.data import charger_serie_horaire
from ocp_ml.features import etat_origine
from ocp_ml.prevision import Prevision

# ============================================
# INITIALISATION
# ============================================
app = FastAPI(
    title="OCP Pipeline API",
    description="API de prediction du débit horaire pipeline Khouribga -> Jorf Lasfar",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# CHARGEMENT MODELES ET DONNEES
# ============================================
# 2 ans apres la derniere mesure (31/12/2024 -> 31/12/2026)
HORIZON_MAX = 24 * 731

df_cache = None
etat_cache = None
prevision = None


def get_data():
    global df_cache, etat_cache
    if df_cache is None:
        try:
            df_cache = charger_serie_horaire()
            etat_cache = etat_origine(df_cache)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur chargement donnees: {str(e)}")
    return df_cache


def get_prevision():
    global prevision
    if prevision is None:
        try:
            prevision = Prevision()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur chargement modeles (lancer train.py): {str(e)}")
    return prevision


def serie_valide():
    """Debit hors arrets operationnels, comme pour l'entrainement."""
    df = get_data()
    s = df[CIBLE]
    return s[s >= SEUIL_ARRET]


def statut_debit(debit):
    if debit > 1600:
        return "eleve"
    elif debit > 1200:
        return "normal"
    return "faible"

# ============================================
# ROUTES
# ============================================

@app.get("/")
def root():
    return {
        "message": "OCP Pipeline API",
        "version": "2.0.0",
        "status": "online"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def get_stats():
    s = serie_valide()
    brut = get_data()[CIBLE].dropna()
    derniers_30j = brut[brut.index > brut.index[-1] - pd.Timedelta(days=30)]
    return {
        "debit_moyen": round(float(s.mean()), 2),
        "debit_max": round(float(s.max()), 2),
        "debit_min": round(float(s.min()), 2),
        "nb_lignes": len(s),
        "periode": f"{s.index.min():%d/%m/%Y} - {s.index.max():%d/%m/%Y}",
        "derniere_date": brut.index[-1].isoformat(),
        "dernier_debit": round(float(brut.iloc[-1]), 2),
        "moyenne_24h": round(float(brut.tail(24).mean()), 2),
        "arrets_30j": int((derniers_30j < SEUIL_ARRET).sum()),
    }

@app.get("/repartition-clients")
def get_repartition_clients(jours: int = 30):
    """Debit moyen par client et volume journalier par client sur les derniers jours."""
    df = get_data()
    clients = ["IMACID", "JFO", "JFD", "JFT", "JFQ", "JFF", "PMP"]
    recent = df[df.index > df.index[-1] - pd.Timedelta(days=jours)][clients]
    journalier = (recent.resample("D").mean() * 24 / 1000).round(2)  # kt/jour
    return {
        "clients": clients,
        "moyennes": {c: round(float(df[c].mean()), 2) for c in clients},
        "journalier": [
            {"date": f"{d:%Y-%m-%d}", **row.to_dict()} for d, row in journalier.iterrows()
        ],
    }

@app.get("/profil-semaine")
def get_profil_semaine():
    """Debit moyen par jour de semaine (0 = lundi) et par heure."""
    s = serie_valide()
    profil = s.groupby([s.index.dayofweek, s.index.hour]).mean().unstack()
    return {
        "jours": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
        "heures": list(range(24)),
        "valeurs": profil.round(1).values.tolist(),
    }

@app.get("/performances")
def get_performances():
    """Metriques de test (nov.-dec. 2024) calculees par train.py, prevision a 1h."""
    meta = get_prevision().meta
    h1 = meta["directs"]["1"]
    long_terme = meta["long_terme"]
    return {
        "r2": h1["test"]["r2"],
        "mae": h1["test"]["mae"],
        "rmse": h1["test"]["rmse"],
        "mae_persistance": h1["references"]["persistance"]["mae"],
        "modele": "XGBoost direct multi-horizon",
        "test_size": h1["test"]["n"],
        "periode_test": f"a partir du {meta['decoupage']['debut_test']}",
        "par_horizon": [
            {
                "horizon": int(h),
                **r["test"],
                "mae_persistance": r["references"]["persistance"]["mae"],
                "mae_meme_heure": r["references"]["meme_heure_connue"]["mae"],
                "mae_moyenne": r["references"]["moyenne"]["mae"],
                "couverture_80": r["couverture_80_test"],
            }
            for h, r in meta["directs"].items()
        ],
        "long_terme": {
            **long_terme["test"],
            "mae_moyenne": long_terme["references"]["moyenne"]["mae"],
            "couverture_80": long_terme["couverture_80_test"],
        },
        "entrainement": {
            "date": meta["date_entrainement"],
            "periode_donnees": meta["periode_donnees"],
            "debut_validation": meta["decoupage"]["debut_validation"],
            "debut_test": meta["decoupage"]["debut_test"],
            "graine": meta["graine"],
            "empreinte_donnees": meta["empreinte_donnees"],
            "versions": meta["versions"],
        },
    }

@app.get("/qualite-donnees")
def get_qualite_donnees():
    """Audit des donnees brutes et de l'ancien pipeline (reports/qualite.json, produit par train.py)."""
    try:
        with open(REPORTS_DIR / "qualite.json", encoding="utf-8") as f:
            qualite = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Rapport qualite absent : lancer train.py")
    h1 = get_prevision().meta["directs"]["1"]
    qualite["nouveau_modele"] = {
        "mae": h1["test"]["mae"],
        "r2": h1["test"]["r2"],
        "mae_persistance": h1["references"]["persistance"]["mae"],
    }
    return qualite

@app.get("/historique")
def get_historique(limit: int = 200):
    s = get_data()[CIBLE].dropna().tail(limit)
    return {
        "timestamps": s.index.astype(str).tolist(),
        "debits": s.round(2).tolist()
    }

@app.get("/debit-par-heure")
def get_debit_par_heure():
    s = serie_valide()
    result = s.groupby(s.index.hour).mean()
    return {
        "heures": result.index.tolist(),
        "debits": result.round(2).tolist()
    }

@app.get("/predict-future")
def predict_future(target_datetime: str):
    """
    Predit le debit a une date/heure future (jusqu'a 2 ans, soit fin 2026).
    0-12h : modeles directs (un par horizon), 12-24h : fondu vers le modele
    long terme (calendaire), au-dela : modele long terme seul.
    target_datetime format attendu: 'YYYY-MM-DDTHH:MM:SS' (ex: 2025-01-02T14:00:00)
    """
    df = get_data()
    prev = get_prevision()

    try:
        target_dt = pd.to_datetime(target_datetime).floor("h")
    except Exception:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DDTHH:MM:SS")

    last_known_ts = df.index[df[CIBLE].notna()][-1]
    hours_ahead = int((target_dt - last_known_ts).total_seconds() // 3600)

    if hours_ahead <= 0:
        if target_dt in df.index and pd.notna(df.at[target_dt, CIBLE]):
            val = float(df.at[target_dt, CIBLE])
            return {
                "debit_predit": round(val, 2),
                "unite": "t/h",
                "statut": statut_debit(val),
                "source": "historique_reel",
                "hours_ahead": 0
            }
        raise HTTPException(status_code=400, detail="Date passee non presente dans l'historique")

    if hours_ahead > HORIZON_MAX:
        raise HTTPException(status_code=400, detail=f"Horizon trop lointain ({hours_ahead}h). Maximum : {HORIZON_MAX // 24} jours.")

    # On prevoit jusqu'a la fin de la journee cible pour en donner le profil complet
    fin_journee = target_dt.normalize() + pd.Timedelta(hours=23)
    n_heures = int((fin_journee - last_known_ts).total_seconds() // 3600)
    _, complete = prev.predire(df, etat_cache, n_heures)
    final = complete.iloc[hours_ahead - 1]
    journee = complete[complete["date"].dt.normalize() == target_dt.normalize()]
    profil_jour = [
        {"heure": int(r.date.hour), "debit": round(float(r.debit), 2), "bas": round(float(r.bas), 2), "haut": round(float(r.haut), 2)}
        for r in journee.itertuples()
    ]
    serie = complete.iloc[:hours_ahead].copy()

    # Pas du graphique : horaire jusqu'a 3 jours, journalier jusqu'a 60 jours, hebdomadaire au-dela
    if hours_ahead > 24 * 60:
        pas_serie = "semaine"
        serie = serie.groupby(serie["date"].dt.to_period("W").dt.start_time).mean(numeric_only=True).reset_index()
        serie["date"] = serie["date"].dt.strftime("%Y-%m-%d")
    elif hours_ahead > 72:
        pas_serie = "jour"
        serie = serie.groupby(serie["date"].dt.floor("D")).mean(numeric_only=True).reset_index()
        serie["date"] = serie["date"].dt.strftime("%Y-%m-%d")
    else:
        pas_serie = "heure"
        serie["date"] = serie["date"].dt.strftime("%Y-%m-%d %H:%M")

    if hours_ahead <= 12:
        fiabilite = "court_terme"
    elif hours_ahead <= prev.horizon_direct:
        fiabilite = "transition"
    else:
        fiabilite = "long_terme"

    return {
        "debit_predit": round(float(final["debit"]), 2),
        "intervalle_bas": round(float(final["bas"]), 2),
        "intervalle_haut": round(float(final["haut"]), 2),
        "unite": "t/h",
        "statut": statut_debit(final["debit"]),
        "source": "prediction",
        "fiabilite": fiabilite,
        "hours_ahead": hours_ahead,
        "derniere_date_connue": str(last_known_ts),
        "serie": serie.round(2).to_dict(orient="records"),
        "pas_serie": pas_serie,
        "profil_jour": profil_jour,
        # Volume prevu sur la journee cible (kt)
        "volume_jour_kt": round(sum(p["debit"] for p in profil_jour) / 1000, 2),
        "heures_profil_jour": len(profil_jour),
    }
