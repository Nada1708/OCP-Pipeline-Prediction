import numpy as np
import pandas as pd
import pytest

from ocp_ml import config as C
from ocp_ml.data import charger_serie_horaire
from ocp_ml.features import assembler_direct, etat_origine
from ocp_ml.modeling import cible_valide, decoupage, nouveau_modele


@pytest.fixture(scope="module")
def df():
    return charger_serie_horaire()


def test_serie_horaire_reguliere_sans_doublons(df):
    assert df.index.is_unique
    assert (np.diff(df.index.values) == np.timedelta64(1, "h")).all()


def test_debit_total_inclut_tous_les_clients(df):
    ok = df[C.CIBLE].notna()
    assert df.loc[ok, "JFT"].notna().all(), "JFT doit etre renseigne sur toute la periode"
    np.testing.assert_allclose(df.loc[ok, C.CIBLE], df.loc[ok, C.DESTINATIONS].sum(axis=1))


def test_aucune_fuite_du_futur(df):
    """Modifier les donnees apres t ne doit changer aucune variable connue a t."""
    t = pd.Timestamp("2024-11-15 12:00")
    modifie = df.copy()
    futur = modifie.index > t
    modifie.loc[futur, C.DESTINATIONS + [C.CIBLE]] *= 3
    modifie.loc[futur, ["vente_realisee", "expedition_j1"]] = 0
    pd.testing.assert_series_equal(etat_origine(df).loc[t], etat_origine(modifie).loc[t])

    X, _ = assembler_direct(df, etat_origine(df), range(1, 25), origines=pd.DatetimeIndex([t]))
    X_mod, _ = assembler_direct(modifie, etat_origine(modifie), range(1, 25), origines=pd.DatetimeIndex([t]))
    pd.testing.assert_frame_equal(X, X_mod)


def test_decoupage_chronologique_sans_recouvrement(df):
    _, meta = assembler_direct(df, etat_origine(df), [24])
    meta = meta[cible_valide(meta["cible"])]
    train, validation, test = decoupage(meta["origine"], meta["cible_ts"])
    assert meta["cible_ts"][train].max() < C.DEBUT_VALIDATION
    assert meta["origine"][validation].min() >= C.DEBUT_VALIDATION
    assert meta["cible_ts"][validation].max() < C.DEBUT_TEST
    assert meta["origine"][test].min() >= C.DEBUT_TEST
    assert not (train & test).any() and not (validation & test).any()


def test_entrainement_reproductible(df):
    X, meta = assembler_direct(df, etat_origine(df), [1])
    garde = cible_valide(meta["cible"]).values
    X, y = X[garde], meta["cible"].values[garde]
    p1 = nouveau_modele(200, arret_precoce=False).fit(X, y).predict(X)
    p2 = nouveau_modele(200, arret_precoce=False).fit(X, y).predict(X)
    np.testing.assert_array_equal(p1, p2)
