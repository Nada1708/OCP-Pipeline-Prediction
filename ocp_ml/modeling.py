"""Entrainement, evaluation et intervalles d'incertitude."""
import numpy as np
from xgboost import XGBRegressor

from .config import DEBUT_TEST, DEBUT_VALIDATION, SEED, SEUIL_ARRET

PARAMS_XGB = {
    "learning_rate": 0.02,
    "max_depth": 4,
    "min_child_weight": 10,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "reg:squarederror",
    "tree_method": "hist",
    "random_state": SEED,
    "n_jobs": 4,
}
N_ARBRES_MAX = 3000
ARRET_PRECOCE = 200

QUANTILES = (0.10, 0.90)  # intervalle a 80%


def cible_valide(cible):
    """Les arrets operationnels (< seuil) ne sont pas previsibles : exclus de l'apprentissage."""
    return cible.notna() & (cible >= SEUIL_ARRET)


def decoupage(origine, cible_ts):
    """Decoupage chronologique sans recouvrement : une ligne d'entrainement ne voit jamais
    une cible situee dans la periode de validation/test."""
    train = cible_ts < DEBUT_VALIDATION
    validation = (origine >= DEBUT_VALIDATION) & (cible_ts < DEBUT_TEST)
    test = origine >= DEBUT_TEST
    return train.values, validation.values, test.values


def metriques(y, p):
    e = y - p
    ss_tot = ((y - y.mean()) ** 2).sum()
    return {
        "mae": round(float(np.abs(e).mean()), 2),
        "rmse": round(float(np.sqrt((e ** 2).mean())), 2),
        "r2": round(float(1 - (e ** 2).sum() / ss_tot), 4),
        "n": int(len(y)),
    }


def quantiles_residus(y, p):
    q_bas, q_haut = np.quantile(y - p, QUANTILES)
    return round(float(q_bas), 2), round(float(q_haut), 2)


def couverture(y, p, q_bas, q_haut):
    return round(float(((y >= p + q_bas) & (y <= p + q_haut)).mean()), 4)


def nouveau_modele(n_arbres=N_ARBRES_MAX, arret_precoce=True):
    return XGBRegressor(
        n_estimators=n_arbres,
        early_stopping_rounds=ARRET_PRECOCE if arret_precoce else None,
        eval_metric="mae",
        **PARAMS_XGB,
    )


def entrainer_et_evaluer(X, y, train, validation, test):
    """1. Choix du nombre d'arbres par arret precoce sur la validation.
    2. Intervalle calibre sur la validation, couverture mesuree sur le test.
    3. Re-entrainement train+validation -> metriques de test.
    4. Modele final sur toutes les donnees (production)."""
    m = nouveau_modele()
    m.fit(X[train], y[train], eval_set=[(X[validation], y[validation])], verbose=False)
    n_arbres = m.best_iteration + 1
    q_val = quantiles_residus(y[validation], m.predict(X[validation]))

    train_val = train | validation
    m_eval = nouveau_modele(n_arbres, arret_precoce=False).fit(X[train_val], y[train_val])
    p_test = m_eval.predict(X[test])
    q_test = quantiles_residus(y[test], p_test)

    m_final = nouveau_modele(n_arbres, arret_precoce=False).fit(X, y)
    resultat = {
        "n_arbres": int(n_arbres),
        "test": metriques(y[test], p_test),
        "couverture_80_test": couverture(y[test], p_test, *q_val),
        # Production : intervalle issu des residus hors echantillon les plus recents
        "residu_q10": q_test[0],
        "residu_q90": q_test[1],
    }
    return m_final, m_eval, p_test, resultat
