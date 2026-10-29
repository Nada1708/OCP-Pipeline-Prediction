"""Configuration centrale du pipeline (chemins, dates de decoupage, graine)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "Data"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"

FICHIER_BRUT = DATA_DIR / "dataset_OCP_pipeline.xlsx"
FICHIER_JFT = DATA_DIR / "Extraction JFT Mai et Juin.xlsx"

# Reproductibilite : une seule graine pour tout le pipeline
SEED = 42

# Debit total = somme des clients desservis (JFT inclus sur toute la periode)
DESTINATIONS = ["IMACID", "IMACID DN200", "JFO", "JFD", "JFT", "JFQ", "JFF", "PMP", "Ligne E DN200"]
CIBLE = "debit_total"

# Sous ce seuil on considere un arret operationnel (non previsible) : exclu de la cible
SEUIL_ARRET = 500

# Trous courts (heures manquantes) combles par interpolation
MAX_HEURES_INTERPOLEES = 3

# Decoupage chronologique fixe (independant du nombre de lignes)
DEBUT_VALIDATION = pd.Timestamp("2024-10-01")
DEBUT_TEST = pd.Timestamp("2024-11-01")

# Prediction multi-horizon directe (un seul modele, horizon en variable)
HORIZONS = list(range(1, 49))
