"""Chargement et nettoyage des donnees brutes en une serie horaire reguliere."""
import warnings

import numpy as np
import pandas as pd

from .config import DESTINATIONS, FICHIER_BRUT, FICHIER_JFT, MAX_HEURES_INTERPOLEES

COLONNES_JOURNALIERES = {
    "Expédition J-1": "expedition_j1",
    "Vente réalisée": "vente_realisee",
    "Total distribué": "total_distribue",
}


def charger_jft_extraction(chemin=FICHIER_JFT):
    """Lit l'extraction JFT (mai-juin). Les feuilles n'ont pas la meme mise en page :
    on repere la colonne de dates puis la premiere colonne numerique a sa droite."""
    series = []
    for feuille in pd.ExcelFile(chemin).sheet_names:
        brut = pd.read_excel(chemin, sheet_name=feuille, header=None)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)  # colonnes non-dates converties en NaT
            dates = brut.apply(lambda c: pd.to_datetime(c, errors="coerce"))
        col_date = dates.notna().sum().idxmax()
        valeurs = brut.iloc[:, col_date + 1:].apply(pd.to_numeric, errors="coerce")
        col_val = valeurs.notna().sum().idxmax()
        s = pd.Series(valeurs[col_val].values, index=dates[col_date]).dropna()
        series.append(s[s.index.notna()])
    jft = pd.concat(series).sort_index()
    return jft[~jft.index.duplicated(keep="first")]


def charger_serie_horaire(chemin_brut=FICHIER_BRUT, chemin_jft=FICHIER_JFT):
    """Retourne un DataFrame indexe par heure (pas regulier), avec :
    - les debits par client et le debit total (JFT inclus partout),
    - les grandeurs journalieres (expedition, vente, total distribue),
    - `interpole` : heure manquante comblee, `manquant` : trou trop long (NaN)."""
    brut = pd.read_excel(chemin_brut, header=2)
    brut = brut.dropna(subset=["Timestamp"])
    # Les fichiers mensuels se chevauchent : lignes identiques en double
    brut = brut.drop_duplicates(subset="Timestamp", keep="first").set_index("Timestamp").sort_index()
    brut = brut.rename(columns={"JFT *": "JFT", **COLONNES_JOURNALIERES})

    numeriques = [c for c in DESTINATIONS + list(COLONNES_JOURNALIERES.values())]
    df = brut[numeriques].apply(pd.to_numeric, errors="coerce")

    # JFT absent de mai-juin dans le fichier principal : complete par l'extraction
    df["JFT"] = df["JFT"].combine_first(charger_jft_extraction(chemin_jft).reindex(df.index))

    index = pd.date_range(df.index.min(), df.index.max(), freq="h", name="timestamp")
    df = df.reindex(index)
    manquant_avant = df[DESTINATIONS].isna().any(axis=1)
    df[DESTINATIONS] = df[DESTINATIONS].interpolate(method="time", limit=MAX_HEURES_INTERPOLEES, limit_area="inside")
    # Bruit capteur (valeurs negatives infimes)
    df[DESTINATIONS] = df[DESTINATIONS].clip(lower=0)

    # Grandeurs journalieres : une valeur par jour, propagee sur les heures du jour
    jour = df.index.normalize()
    for c in COLONNES_JOURNALIERES.values():
        df[c] = df[c].groupby(jour).transform("first")

    df["debit_total"] = df[DESTINATIONS].sum(axis=1, min_count=len(DESTINATIONS))
    df["manquant"] = df["debit_total"].isna()
    df["interpole"] = manquant_avant & ~df["manquant"]
    return df


def jours_feries(index):
    """Jours feries marocains (fixes + religieux 2024-2026, dates approximatives a +/- 1 jour)."""
    fixes = {"01-01", "01-11", "01-14", "05-01", "07-30", "08-14", "08-20", "08-21", "11-06", "11-18"}
    religieux = {
        "2024-04-10", "2024-04-11", "2024-06-17", "2024-06-18", "2024-07-08", "2024-09-16", "2024-09-17",
        "2025-03-31", "2025-04-01", "2025-06-07", "2025-06-08", "2025-06-27", "2025-09-05", "2025-09-06",
        "2026-03-20", "2026-03-21", "2026-05-27", "2026-05-28", "2026-06-17", "2026-08-26", "2026-08-27",
    }
    md = index.strftime("%m-%d")
    ymd = index.strftime("%Y-%m-%d")
    return np.isin(md, list(fixes)) | np.isin(ymd, list(religieux))
