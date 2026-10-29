"""Audit de la qualite des donnees et de l'ancien pipeline (avant / apres)."""
import numpy as np
import pandas as pd

from .config import DATA_DIR, DESTINATIONS, FICHIER_BRUT, SEUIL_ARRET

ANCIEN_DATASET = DATA_DIR / "OCP_Dataset_ML.xlsx"
ANCIEN_MODELE = DATA_DIR / "model_xgboost_ocp_v3.json"
ANCIENNES_FEATURES = [
    "Heure (0-23)", "Jour semaine (0-6)", "Mois (1-12)", "Jour mois", "Weekend (0/1)",
    "Heure sin", "Heure cos",
    "Lag 1h (t/h)", "Lag 2h (t/h)", "Lag 3h (t/h)",
    "Lag 6h (t/h)", "Lag 12h (t/h)", "Lag 24h (t/h)",
    "Rolling 3h (t/h)", "Rolling 6h (t/h)", "Rolling 12h (t/h)", "Rolling 24h (t/h)",
    "Std 6h (t/h)", "Vente/heure (TSM)",
    "débit_lag_48h", "débit_lag_168h", "diff_1h", "diff_24h", "Expédition J-1",
]


def auditer_brut(df):
    """Problemes trouves dans le fichier brut et corriges par charger_serie_horaire (df)."""
    brut = pd.read_excel(FICHIER_BRUT, header=2).dropna(subset=["Timestamp"])
    jft = pd.to_numeric(brut.drop_duplicates("Timestamp")["JFT *"], errors="coerce")
    ts = brut.drop_duplicates("Timestamp")["Timestamp"]
    return {
        "lignes_brutes": int(len(brut)),
        "doublons": int(brut["Timestamp"].duplicated().sum()),
        "heures_manquantes": int(len(pd.date_range(ts.min(), ts.max(), freq="h").difference(ts))),
        "heures_interpolees": int(df["interpole"].sum()),
        "heures_vides": int(df["manquant"].sum()),
        "jft_absent_heures": int(jft.isna().sum()),
        "jft_absent_periode": f"{ts[jft.isna()].min():%d/%m/%Y} -> {ts[jft.isna()].max():%d/%m/%Y}",
        "jft_moyen": round(float(df["JFT"].mean()), 1),
        "heures_serie_finale": int(df["debit_total"].notna().sum()),
        "heures_arret": int((df["debit_total"] < SEUIL_ARRET).sum()),
    }


def auditer_ancien_pipeline(df):
    """Mesure les defauts de l'ancien dataset ML et de l'ancien modele XGBoost v3."""
    if not (ANCIEN_DATASET.exists() and ANCIEN_MODELE.exists()):
        return None
    from xgboost import XGBRegressor

    ancien = pd.read_excel(ANCIEN_DATASET, header=2)
    cible = ancien["Débit total (t/h)"]
    sans_doublons = ancien.drop_duplicates("Timestamp").set_index("Timestamp")

    # Cible : comparee a la somme des clients du brut, avec et sans JFT
    commun = sans_doublons.index.intersection(df.index)
    ancienne_cible = sans_doublons.loc[commun, "Débit total (t/h)"]
    clients_sans_jft = df.loc[commun, [c for c in DESTINATIONS if c != "JFT"]].sum(axis=1)
    clients_avec_jft = df.loc[commun, DESTINATIONS].sum(axis=1)

    # Vente/heure = ventes realisees du jour meme / 24 : connue seulement en fin de journee
    brut = pd.read_excel(FICHIER_BRUT, header=2).dropna(subset=["Timestamp"]).drop_duplicates("Timestamp").set_index("Timestamp")
    vente_jour = (brut["Vente réalisée"] / 24).reindex(sans_doublons.index)
    fuite = np.isclose(sans_doublons["Vente/heure (TSM)"], vente_jour, rtol=1e-3).mean()

    # Reproduction de l'evaluation de l'ancien modele (meme preparation que l'ancienne API)
    d = ancien.copy()
    d["débit_lag_48h"] = cible.shift(48)
    d["débit_lag_168h"] = cible.shift(168)
    decale = cible.shift(1)
    d["diff_1h"] = decale.diff(1)
    d["diff_24h"] = decale.diff(24)
    d = d.dropna().reset_index(drop=True)
    exp = brut["Expédition J-1"].rename("Expédition J-1").reset_index()
    d = d.merge(exp, on="Timestamp", how="left").dropna().reset_index(drop=True)
    d = d[d["Débit total (t/h)"] >= SEUIL_ARRET].reset_index(drop=True)
    test = d.iloc[int(len(d) * 0.8):]
    y = test["Débit total (t/h)"].values

    m = XGBRegressor()
    m.load_model(ANCIEN_MODELE)
    importance = pd.Series(m.feature_importances_, index=ANCIENNES_FEATURES).sort_values(ascending=False)

    heures_perdues = df.index[df["debit_total"].notna()].difference(sans_doublons.index)
    return {
        "lignes": int(len(ancien)),
        "doublons": int(ancien["Timestamp"].duplicated().sum()),
        "heures_perdues": int(len(heures_perdues)),
        "plus_long_trou": _plus_long_trou(sans_doublons.index),
        # ~0 sans JFT, ~JFT avec : l'ancienne cible n'inclut jamais JFT
        "ecart_median_cible_sans_jft": round(float((ancienne_cible - clients_sans_jft).abs().median()), 1),
        "ecart_median_cible_avec_jft": round(float((ancienne_cible - clients_avec_jft).abs().median()), 1),
        "part_vente_jour_meme": round(float(fuite), 3),
        "rang_variable_mois": int(list(importance.index).index("Mois (1-12)") + 1),
        "mae_ancien_modele": round(float(np.abs(m.predict(test[ANCIENNES_FEATURES]) - y).mean()), 2),
        "mae_persistance": round(float(np.abs(test["Lag 1h (t/h)"].values - y).mean()), 2),
        "periode_test": f"{test['Timestamp'].min():%d/%m/%Y} -> {test['Timestamp'].max():%d/%m/%Y}",
        "r2_annonce": 0.96,
        "mae_annoncee": 14,
    }


def _plus_long_trou(index):
    ecarts = pd.Series(index[1:] - index[:-1], index=index[1:])
    fin = ecarts.idxmax()
    return {"debut": f"{fin - ecarts.max():%d/%m/%Y}", "fin": f"{fin:%d/%m/%Y}", "jours": round(ecarts.max() / pd.Timedelta(days=1), 1)}
