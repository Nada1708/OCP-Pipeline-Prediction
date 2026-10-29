"""Construction des variables explicatives.

Strategie directe multi-horizon : a partir d'une origine t (derniere heure connue),
on predit le debit a t+h avec un seul modele qui recoit l'horizon h en variable.
Toutes les variables d'etat n'utilisent que des donnees <= t (aucune fuite).
"""
import numpy as np
import pandas as pd

from .config import CIBLE, DESTINATIONS, SEUIL_ARRET
from .data import jours_feries

LAGS = [1, 2, 3, 6, 12, 23, 47, 167]
FENETRES = [3, 6, 12, 24]


def etat_origine(df):
    """Variables connues a l'heure t, pour chaque heure t de la serie."""
    y = df[CIBLE]
    f = pd.DataFrame(index=df.index)
    f["debit_t"] = y
    for k in LAGS:
        f[f"debit_t_moins_{k}h"] = y.shift(k)
    for w in FENETRES:
        f[f"moyenne_{w}h"] = y.rolling(w).mean()
    f["ecart_type_6h"] = y.rolling(6).std()
    f["ecart_type_24h"] = y.rolling(24).std()
    f["variation_1h"] = y - y.shift(1)
    f["variation_24h"] = y - y.shift(24)
    f["nb_arrets_24h"] = (y < SEUIL_ARRET).astype(float).where(y.notna()).rolling(24, min_periods=1).sum()
    for c in DESTINATIONS:
        f[f"{c}_t"] = df[c]
    # Grandeurs journalieres connues en debut de journee
    f["expedition_j1"] = df["expedition_j1"]
    f["vente_j1"] = df["vente_realisee"].shift(24)
    return f


def calendrier(index):
    heure = index.hour.values
    jour = index.dayofweek.values
    return pd.DataFrame({
        "heure": heure,
        "heure_sin": np.sin(2 * np.pi * heure / 24),
        "heure_cos": np.cos(2 * np.pi * heure / 24),
        "jour_semaine": jour,
        "weekend": (jour >= 5).astype(int),
        "ferie": jours_feries(index).astype(int),
    })


def assembler_direct(df, etat, horizons, origines=None):
    """Empile (origine, horizon) -> une ligne. Retourne X, la date cible et la cible."""
    y = df[CIBLE]
    if origines is None:
        origines = etat.index[etat["debit_t"].notna()]
    blocs = []
    for h in horizons:
        cible_ts = origines + pd.Timedelta(hours=h)
        bloc = etat.loc[origines].reset_index(drop=True)
        bloc = pd.concat([bloc, calendrier(cible_ts)], axis=1)
        bloc["horizon"] = h
        # Derniere valeur connue a la meme heure (J-1 si h <= 24, J-2 si h <= 48, ...)
        recul = pd.Timedelta(hours=24 * int(np.ceil(h / 24)))
        bloc["debit_meme_heure_connu"] = y.reindex(cible_ts - recul).values
        bloc["debit_cible_moins_168h"] = y.reindex(cible_ts - pd.Timedelta(hours=168)).values
        bloc["origine"] = origines
        bloc["cible_ts"] = cible_ts
        bloc["cible"] = y.reindex(cible_ts).values
        blocs.append(bloc)
    tout = pd.concat(blocs, ignore_index=True)
    meta = tout[["origine", "cible_ts", "cible"]]
    return tout.drop(columns=["origine", "cible_ts", "cible"]), meta


def features_long_terme(index):
    """Modele long terme : uniquement le calendrier (mois exclu, seuls mai-decembre sont observes)."""
    return calendrier(index)
