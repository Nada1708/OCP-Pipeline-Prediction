from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings("ignore")

# ============================================
# INITIALISATION
# ============================================
app = FastAPI(
    title="OCP Pipeline API",
    description="API de prediction du débit horaire pipeline Khouribga -> Jorf Lasfar",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ============================================
# CHARGEMENT MODELE ET DONNEES
# ============================================
model = None
df_cache = None

def get_model():
    global model
    if model is None:
        try:
            model = XGBRegressor()
            model.load_model("../Data/model_xgboost_ocp_v3.json")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur chargement modele: {str(e)}")
    return model

def get_data():
    global df_cache
    if df_cache is None:
        try:
            df = pd.read_excel("../Data/OCP_Dataset_ML.xlsx", header=2)
            df["débit_lag_48h"]  = df["Débit total (t/h)"].shift(48)
            df["débit_lag_168h"] = df["Débit total (t/h)"].shift(168)
            df["diff_1h"]        = df["Débit total (t/h)"].diff(1)
            df["diff_24h"]       = df["Débit total (t/h)"].diff(24)
            df_cache = df.dropna().reset_index(drop=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur chargement donnees: {str(e)}")
    return df_cache

FEATURES = [
    "Heure (0-23)", "Jour semaine (0-6)", "Mois (1-12)", "Jour mois", "Weekend (0/1)",
    "Heure sin", "Heure cos",
    "Lag 1h (t/h)", "Lag 2h (t/h)", "Lag 3h (t/h)",
    "Lag 6h (t/h)", "Lag 12h (t/h)", "Lag 24h (t/h)",
    "Rolling 3h (t/h)", "Rolling 6h (t/h)", "Rolling 12h (t/h)", "Rolling 24h (t/h)",
    "Std 6h (t/h)", "Vente/heure (TSM)",
    "débit_lag_48h", "débit_lag_168h", "diff_1h", "diff_24h"
]

# ============================================
# SCHEMAS
# ============================================
class PredictionInput(BaseModel):
    heure: int
    jour_semaine: int
    mois: int
    jour_mois: int
    est_weekend: int
    lag_1h: float
    lag_2h: float
    lag_3h: float
    lag_6h: float
    lag_12h: float
    lag_24h: float
    rolling_3h: float
    rolling_6h: float
    rolling_12h: float
    rolling_24h: float
    std_6h: float
    vente_heure: float
    lag_48h: float
    lag_168h: float
    diff_1h: float
    diff_24h: float

# ============================================
# ROUTES
# ============================================

@app.get("/")
def root():
    return {
        "message": "OCP Pipeline API",
        "version": "1.0.0",
        "status": "online"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict(data: PredictionInput):
    m = get_model()

    heure_sin = np.sin(2 * np.pi * data.heure / 24)
    heure_cos = np.cos(2 * np.pi * data.heure / 24)

    X = pd.DataFrame([[
        data.heure, data.jour_semaine, data.mois, data.jour_mois, data.est_weekend,
        heure_sin, heure_cos,
        data.lag_1h, data.lag_2h, data.lag_3h, data.lag_6h, data.lag_12h, data.lag_24h,
        data.rolling_3h, data.rolling_6h, data.rolling_12h, data.rolling_24h,
        data.std_6h, data.vente_heure, data.lag_48h, data.lag_168h,
        data.diff_1h, data.diff_24h
    ]], columns=FEATURES)

    prediction = float(m.predict(X)[0])

    if prediction > 1600:
        statut = "eleve"
    elif prediction > 1200:
        statut = "normal"
    else:
        statut = "faible"

    return {
        "débit_predit": round(prediction, 2),
        "unite": "t/h",
        "statut": statut
    }

@app.get("/stats")
def get_stats():
    df = get_data()
    return {
        "debit_moyen": round(float(df["Débit total (t/h)"].mean()), 2),
        "debit_max": round(float(df["Débit total (t/h)"].max()), 2),
        "debit_min": round(float(df["Débit total (t/h)"].min()), 2),
        "nb_lignes": len(df),
        "periode": "Mai 2024 - Decembre 2024"
    }

@app.get("/performances")
def get_performances():
    df = get_data()
    m = get_model()

    X = df[FEATURES]
    y = df["Débit total (t/h)"]
    split = int(len(df) * 0.8)
    X_test = X.iloc[split:]
    y_test = y.iloc[split:]
    y_pred = m.predict(X_test)

    return {
        "r2": round(float(r2_score(y_test, y_pred)), 4),
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 2),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
        "modele": "XGBoost v3",
        "train_size": split,
        "test_size": len(X_test)
    }

@app.get("/historique")
def get_historique(limit: int = 200):
    df = get_data()
    data = df[["Timestamp", "Débit total (t/h)"]].tail(limit)
    return {
        "timestamps": data["Timestamp"].astype(str).tolist(),
        "débits": data["Débit total (t/h)"].tolist()
    }

@app.get("/débit-par-heure")
def get_débit_par_heure():
    df = get_data()
    result = df.groupby("Heure (0-23)")["Débit total (t/h)"].mean().reset_index()
    return {
        "heures": result["Heure (0-23)"].tolist(),
        "débits": result["Débit total (t/h)"].round(2).tolist()
    }