"""Validation glissante : le pipeline est re-entraine pour plusieurs mois de test successifs.

    py -3.12 backtest.py

Pour chaque mois M : entrainement sur les donnees avant M-1, validation sur M-1, test sur M.
Mesure la stabilite des performances d'une periode a l'autre. Produit reports/backtest.json.
"""
import json

import numpy as np
import pandas as pd

from ocp_ml import config as C
from ocp_ml.data import charger_serie_horaire
from ocp_ml.features import assembler_direct, etat_origine
from ocp_ml.modeling import cible_valide, metriques, nouveau_modele

MOIS_TEST = ["2024-09", "2024-10", "2024-11", "2024-12"]
HORIZONS = [1, 3, 6, 12, 24]


def main():
    df = charger_serie_horaire()
    etat = etat_origine(df)
    resultats = []
    for mois in MOIS_TEST:
        debut_test = pd.Timestamp(mois)
        debut_val = debut_test - pd.DateOffset(months=1)
        fin_test = debut_test + pd.DateOffset(months=1)
        for h in HORIZONS:
            X, meta = assembler_direct(df, etat, [h])
            garde = cible_valide(meta["cible"]).values
            X, meta = X[garde].drop(columns=["horizon"]).reset_index(drop=True), meta[garde].reset_index(drop=True)
            y = meta["cible"].values
            train = (meta["cible_ts"] < debut_val).values
            val = ((meta["origine"] >= debut_val) & (meta["cible_ts"] < debut_test)).values
            test = ((meta["origine"] >= debut_test) & (meta["cible_ts"] < fin_test)).values

            m = nouveau_modele().fit(X[train], y[train], eval_set=[(X[val], y[val])], verbose=False)
            n_arbres = m.best_iteration + 1
            m = nouveau_modele(n_arbres, arret_precoce=False).fit(X[train | val], y[train | val])
            res = metriques(y[test], m.predict(X[test]))
            pers = metriques(y[test], X["debit_t"].values[test])
            resultats.append({"mois_test": mois, "horizon": h, **res, "mae_persistance": pers["mae"],
                              "gain_pct": round(float((1 - res["mae"] / pers["mae"]) * 100), 1)})
            print(f"{mois} h{h:02d}  MAE {res['mae']:6.1f}  persistance {pers['mae']:6.1f}  gain {resultats[-1]['gain_pct']:5.1f} %")

    r = pd.DataFrame(resultats)
    synthese = r.groupby("horizon").agg(mae_moy=("mae", "mean"), mae_std=("mae", "std"), r2_moy=("r2", "mean"),
                                         gain_moy=("gain_pct", "mean"), gain_min=("gain_pct", "min")).round(2)
    print(synthese)
    with open(C.REPORTS_DIR / "backtest.json", "w", encoding="utf-8") as f:
        json.dump({"mois_test": MOIS_TEST, "resultats": resultats,
                   "synthese": synthese.reset_index().to_dict(orient="records")}, f, indent=2, ensure_ascii=False)
    figure(r)


def figure(r):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    noms = {"2024-09": "Septembre", "2024-10": "Octobre", "2024-11": "Novembre", "2024-12": "Décembre"}
    largeur = 0.2
    x = np.arange(len(HORIZONS))
    plt.figure(figsize=(10, 4.8))
    for i, (mois, couleur) in enumerate(zip(MOIS_TEST, ["#9fd3b4", "#4fae7a", "#00843D", "#00612d"])):
        gains = r[r["mois_test"] == mois].set_index("horizon").loc[HORIZONS, "gain_pct"]
        plt.bar(x + (i - 1.5) * largeur, gains, largeur, color=couleur, label=noms[mois])
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xticks(x, [f"{h} h" for h in HORIZONS])
    plt.xlabel("Horizon de prévision")
    plt.ylabel("Réduction de la MAE vs persistance (%)")
    plt.title("Gain du modèle sur la persistance, pour 4 mois de test successifs")
    plt.legend(title="Mois de test")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(C.REPORTS_DIR / "backtest_gain.png", dpi=150)
    plt.close()


if __name__ == "__main__":
    main()
