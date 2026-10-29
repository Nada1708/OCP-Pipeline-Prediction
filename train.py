"""Entrainement complet et reproductible du pipeline de prevision.

    py -3.12 train.py

Produit :
  models/   modeles XGBoost (un par horizon 1..24h + long terme) et metadata.json
  reports/  metrics.json et figures d'evaluation
"""
import hashlib
import json
import platform
import random
import time

import numpy as np
import pandas as pd
import sklearn
import xgboost

from ocp_ml import config as C
from ocp_ml.data import charger_serie_horaire
from ocp_ml.qualite import auditer_ancien_pipeline, auditer_brut
from ocp_ml.features import assembler_direct, etat_origine, features_long_terme
from ocp_ml.modeling import (PARAMS_XGB, cible_valide, decoupage, entrainer_et_evaluer, metriques,
                             nouveau_modele, quantiles_residus, couverture)

HORIZON_DIRECT_MAX = 24


def empreinte(chemin):
    return hashlib.sha256(chemin.read_bytes()).hexdigest()[:16]


def evaluer_references(X, y, train_val, test):
    """Modeles de reference : tout modele doit faire mieux qu'eux pour etre utile."""
    meme_heure = X["debit_meme_heure_connu"].fillna(X["debit_t"]).values
    return {
        "persistance": metriques(y[test], X["debit_t"].values[test]),
        "meme_heure_connue": metriques(y[test], meme_heure[test]),
        "moyenne": metriques(y[test], np.full(test.sum(), y[train_val].mean())),
    }


def main():
    random.seed(C.SEED)
    np.random.seed(C.SEED)
    debut = time.time()
    C.MODELS_DIR.mkdir(exist_ok=True)
    C.REPORTS_DIR.mkdir(exist_ok=True)

    df = charger_serie_horaire()
    etat = etat_origine(df)
    print(f"Serie horaire : {df.index.min()} -> {df.index.max()} ({len(df)} h, "
          f"{int(df['interpole'].sum())} interpolees, {int(df['manquant'].sum())} manquantes)")

    # ===== MODELES DIRECTS 1..24h =====
    directs, predictions_test, importance_h1 = {}, {}, None
    features_directes = None
    for h in range(1, HORIZON_DIRECT_MAX + 1):
        X, meta = assembler_direct(df, etat, [h])
        garde = cible_valide(meta["cible"]).values
        X, meta = X[garde].reset_index(drop=True), meta[garde].reset_index(drop=True)
        X = X.drop(columns=["horizon"])
        features_directes = list(X.columns)
        y = meta["cible"].values
        train, validation, test = decoupage(meta["origine"], meta["cible_ts"])

        m_final, m_eval, p_test, res = entrainer_et_evaluer(X, y, train, validation, test)
        res["references"] = evaluer_references(X, y, train | validation, test)
        directs[str(h)] = res
        m_final.save_model(C.MODELS_DIR / f"direct_h{h:02d}.json")
        predictions_test[h] = pd.DataFrame({"date": meta["cible_ts"][test].values, "reel": y[test], "predit": p_test})
        if h == 1:
            importance_h1 = pd.Series(m_eval.feature_importances_, index=X.columns).sort_values(ascending=False)
        print(f"  h{h:02d}  MAE {res['test']['mae']:6.1f}  R2 {res['test']['r2']:6.3f}  "
              f"| persistance {res['references']['persistance']['mae']:6.1f}  moyenne {res['references']['moyenne']['mae']:6.1f}"
              f"  | couverture 80% {res['couverture_80_test']:.2f}")

    # ===== MODELE LONG TERME (calendaire) =====
    serie = df.loc[cible_valide(df[C.CIBLE]), C.CIBLE]
    X_long = features_long_terme(serie.index)
    y_long = serie.values
    origine = pd.Series(serie.index, index=serie.index)
    train, validation, test = decoupage(origine, origine)
    _, m_long_eval, p_long, res_long = entrainer_et_evaluer(X_long, y_long, train, validation, test)
    m_long = nouveau_modele(res_long["n_arbres"], arret_precoce=False).fit(X_long, y_long)
    m_long.save_model(C.MODELS_DIR / "long_terme.json")
    res_long["features"] = list(X_long.columns)
    res_long["references"] = {"moyenne": metriques(y_long[test], np.full(test.sum(), y_long[train | validation].mean()))}
    print(f"  long terme  MAE {res_long['test']['mae']:6.1f}  | moyenne {res_long['references']['moyenne']['mae']:6.1f}"
          f"  | couverture 80% {res_long['couverture_80_test']:.2f}")

    # ===== SAUVEGARDE =====
    metadata = {
        "date_entrainement": pd.Timestamp.now().isoformat(timespec="seconds"),
        "derniere_donnee": str(df.index[df[C.CIBLE].notna()][-1]),
        "periode_donnees": f"{df.index.min():%Y-%m-%d} -> {df.index.max():%Y-%m-%d}",
        "decoupage": {"debut_validation": str(C.DEBUT_VALIDATION.date()), "debut_test": str(C.DEBUT_TEST.date())},
        "graine": C.SEED,
        "params_xgb": PARAMS_XGB,
        "seuil_arret": C.SEUIL_ARRET,
        "empreinte_donnees": {p.name: empreinte(p) for p in (C.FICHIER_BRUT, C.FICHIER_JFT)},
        "versions": {"python": platform.python_version(), "xgboost": xgboost.__version__,
                     "pandas": pd.__version__, "scikit-learn": sklearn.__version__},
        "horizon_direct_max": HORIZON_DIRECT_MAX,
        "features_directes": features_directes,
        "directs": directs,
        "long_terme": res_long,
    }
    with open(C.MODELS_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    with open(C.REPORTS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump({k: metadata[k] for k in ("periode_donnees", "decoupage", "empreinte_donnees", "directs", "long_terme")},
                  f, indent=2, ensure_ascii=False)

    qualite = {"brut": auditer_brut(df), "ancien_pipeline": auditer_ancien_pipeline(df)}
    with open(C.REPORTS_DIR / "qualite.json", "w", encoding="utf-8") as f:
        json.dump(qualite, f, indent=2, ensure_ascii=False)

    figures(directs, res_long, predictions_test, importance_h1)
    journaliser_mlflow(metadata)
    print(f"Termine en {time.time() - debut:.0f} s. Modeles dans {C.MODELS_DIR}, rapport dans {C.REPORTS_DIR}")


def figures(directs, res_long, predictions_test, importance_h1):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    h = [int(k) for k in directs]
    plt.figure(figsize=(10, 5))
    plt.plot(h, [directs[str(i)]["test"]["mae"] for i in h], "o-", color="#00843D", label="XGBoost direct")
    plt.plot(h, [directs[str(i)]["references"]["persistance"]["mae"] for i in h], "--", color="#C55A11", label="Persistance")
    plt.plot(h, [directs[str(i)]["references"]["meme_heure_connue"]["mae"] for i in h], ":", color="#7F7F7F", label="Même heure connue")
    plt.axhline(directs["1"]["references"]["moyenne"]["mae"], color="#2E75B6", linestyle="-.", label="Moyenne")
    plt.axhline(res_long["test"]["mae"], color="#00843D", alpha=0.4, label="Modèle long terme")
    plt.xlabel("Horizon de prévision (h)")
    plt.ylabel("MAE sur le test (t/h)")
    plt.title("Erreur selon l'horizon — test nov.–déc. 2024")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(C.REPORTS_DIR / "mae_par_horizon.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 4.5))
    plt.bar(h, [directs[str(i)]["couverture_80_test"] * 100 for i in h], color="#00843D")
    plt.axhline(80, color="#C55A11", linestyle="--", label="Cible : 80 %")
    plt.ylim(50, 100)
    plt.xlabel("Horizon de prévision (h)")
    plt.ylabel("Couverture sur le test (%)")
    plt.title("Part des valeurs réelles comprises dans la fourchette à 80 %")
    plt.legend()
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(C.REPORTS_DIR / "couverture_80.png", dpi=150)
    plt.close()

    p = predictions_test[1].iloc[:24 * 14]
    plt.figure(figsize=(14, 5))
    plt.plot(p["date"], p["reel"], color="#2E75B6", linewidth=1.2, label="Réel")
    plt.plot(p["date"], p["predit"], color="#C55A11", linewidth=1.2, linestyle="--", label="Prédit (h+1)")
    plt.title("Débit réel vs prédit à 1h — 2 premières semaines du test")
    plt.ylabel("Débit total (t/h)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(C.REPORTS_DIR / "reel_vs_predit_h1.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 6))
    importance_h1.head(15).plot(kind="barh", color="#00843D")
    plt.gca().invert_yaxis()
    plt.title("Top 15 des variables — modèle à 1h")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.savefig(C.REPORTS_DIR / "importance_h1.png", dpi=150)
    plt.close()


def journaliser_mlflow(metadata):
    try:
        import mlflow
    except ImportError:
        print("mlflow non installe : run non enregistre")
        return
    mlflow.set_tracking_uri(f"sqlite:///{(C.ROOT / 'mlflow.db').as_posix()}")
    mlflow.set_experiment("OCP_Pipeline_Débit")
    with mlflow.start_run(run_name="XGBoost_direct_multi_horizon"):
        mlflow.log_params({**metadata["params_xgb"], "horizon_direct_max": metadata["horizon_direct_max"],
                           **{f"donnees_{k}": v for k, v in metadata["empreinte_donnees"].items()}})
        for h, res in metadata["directs"].items():
            for nom in ("mae", "rmse", "r2"):
                mlflow.log_metric(f"{nom}_test", res["test"][nom], step=int(h))
            mlflow.log_metric("mae_persistance", res["references"]["persistance"]["mae"], step=int(h))
        mlflow.log_metric("mae_long_terme", metadata["long_terme"]["test"]["mae"])
        mlflow.log_artifacts(str(C.MODELS_DIR), artifact_path="models")
        mlflow.log_artifacts(str(C.REPORTS_DIR), artifact_path="reports")


if __name__ == "__main__":
    main()
