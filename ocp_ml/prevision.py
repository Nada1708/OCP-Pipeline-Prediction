"""Service de prevision utilise par l'API : charge les modeles entraines par train.py."""
import json

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from .config import MODELS_DIR
from .features import assembler_direct, features_long_terme

# Au-dela de DEBUT_FONDU, la prevision directe glisse progressivement vers le modele long terme
DEBUT_FONDU = 12


class Prevision:
    def __init__(self, dossier=MODELS_DIR):
        with open(dossier / "metadata.json", encoding="utf-8") as f:
            self.meta = json.load(f)
        self.horizon_direct = self.meta["horizon_direct_max"]
        self.modeles_directs = {}
        for h in range(1, self.horizon_direct + 1):
            m = XGBRegressor()
            m.load_model(dossier / f"direct_h{h:02d}.json")
            self.modeles_directs[h] = m
        self.modele_long = XGBRegressor()
        self.modele_long.load_model(dossier / "long_terme.json")

    def predire(self, df, etat, n_heures):
        """Prevision horaire de t+1 a t+n_heures depuis la derniere heure connue t."""
        origine = etat.index[etat["debit_t"].notna()][-1]
        horizons = np.arange(1, n_heures + 1)
        cibles = origine + pd.to_timedelta(horizons, unit="h")

        meta_long = self.meta["long_terme"]
        pred = self.modele_long.predict(features_long_terme(cibles)[meta_long["features"]]).astype(float)
        bas = pred + meta_long["residu_q10"]
        haut = pred + meta_long["residu_q90"]

        n_direct = min(n_heures, self.horizon_direct)
        X, _ = assembler_direct(df, etat, range(1, n_direct + 1), origines=pd.DatetimeIndex([origine]))
        colonnes = self.meta["features_directes"]
        for i, h in enumerate(range(1, n_direct + 1)):
            info = self.meta["directs"][str(h)]
            p = float(self.modeles_directs[h].predict(X.iloc[[i]][colonnes])[0])
            poids = min(max((h - DEBUT_FONDU) / (self.horizon_direct - DEBUT_FONDU), 0), 1)
            bas[i] = (1 - poids) * (p + info["residu_q10"]) + poids * bas[i]
            haut[i] = (1 - poids) * (p + info["residu_q90"]) + poids * haut[i]
            pred[i] = (1 - poids) * p + poids * pred[i]

        return origine, pd.DataFrame({"date": cibles, "debit": pred, "bas": bas, "haut": haut})
