import requests

def test_api_stats():
    response = requests.get("http://127.0.0.1:8000/stats")
    assert response.status_code == 200
    data = response.json()
    assert "debit_moyen" in data
    assert "nb_lignes" in data
    print("✅ Stats OK")

def test_api_prediction():
    payload = {
        "heure": 8, "jour_semaine": 0, "mois": 6, "jour_mois": 15,
        "est_weekend": 0, "lag_1h": 1500.0, "lag_2h": 1480.0,
        "lag_3h": 1460.0, "lag_6h": 1450.0, "lag_12h": 1440.0,
        "lag_24h": 1500.0, "rolling_3h": 1480.0, "rolling_6h": 1470.0,
        "rolling_12h": 1460.0, "rolling_24h": 1450.0, "std_6h": 30.0,
        "vente_heure": 2500.0, "lag_48h": 1490.0, "lag_168h": 1500.0,
        "diff_1h": 20.0, "diff_24h": 0.0
    }
    response = requests.post("http://127.0.0.1:8000/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "debit_predit" in data
    assert 0 < data["debit_predit"] < 3000
    print(f"✅ Prédiction OK : {data['debit_predit']} t/h")