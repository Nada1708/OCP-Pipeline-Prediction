import sys

import pytest
from fastapi.testclient import TestClient

from ocp_ml.config import MODELS_DIR, ROOT

pytestmark = pytest.mark.skipif(not (MODELS_DIR / "metadata.json").exists(), reason="lancer train.py d'abord")

sys.path.insert(0, str(ROOT / "backend"))
from main import app  # noqa: E402

client = TestClient(app)


def test_stats():
    data = client.get("/stats").json()
    assert data["nb_lignes"] > 0
    assert data["debit_min"] <= data["debit_moyen"] <= data["debit_max"]


def test_performances_meilleures_que_persistance():
    data = client.get("/performances").json()
    assert data["mae"] < data["mae_persistance"]


@pytest.mark.parametrize("cible, fiabilite", [
    ("2025-01-01T03:00:00", "court_terme"),
    ("2025-01-01T18:00:00", "transition"),
    ("2025-12-31T12:00:00", "long_terme"),
])
def test_prediction_future(cible, fiabilite):
    r = client.get("/predict-future", params={"target_datetime": cible})
    assert r.status_code == 200
    data = r.json()
    assert data["fiabilite"] == fiabilite
    assert data["intervalle_bas"] <= data["debit_predit"] <= data["intervalle_haut"]
    assert 0 < data["debit_predit"] < 4000


def test_prediction_identique_a_chaque_appel():
    params = {"target_datetime": "2025-01-01T06:00:00"}
    assert client.get("/predict-future", params=params).json() == client.get("/predict-future", params=params).json()


def test_qualite_donnees():
    data = client.get("/qualite-donnees").json()
    assert data["brut"]["doublons"] > 0
    assert data["nouveau_modele"]["mae"] < data["nouveau_modele"]["mae_persistance"]


def test_horizon_trop_lointain():
    assert client.get("/predict-future", params={"target_datetime": "2027-06-01T00:00:00"}).status_code == 400
