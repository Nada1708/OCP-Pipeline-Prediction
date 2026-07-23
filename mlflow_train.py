import pandas as pd
import numpy as np
import mlflow
import mlflow.xgboost
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings("ignore")

# 1. Chargement des donnees
df = pd.read_excel("Data/OCP_Dataset_ML.xlsx", header=2)

df["débit_lag_48h"]  = df["Débit total (t/h)"].shift(48)
df["débit_lag_168h"] = df["Débit total (t/h)"].shift(168)
df["diff_1h"]        = df["Débit total (t/h)"].diff(1)
df["diff_24h"]       = df["Débit total (t/h)"].diff(24)
df = df.dropna().reset_index(drop=True)
# ===== INTEGRATION JFT CORRIGE =====
xl_jft = pd.ExcelFile("Data/Extraction JFT Mai et Juin.xlsx")
dfs_jft = []
for sheet in xl_jft.sheet_names:
    df_j = pd.read_excel(xl_jft, sheet_name=sheet, header=None)
    data = df_j.iloc[6:, [4, 5]].copy()
    data.columns = ['timestamp', 'JFT_corrige']
    data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
    data = data.dropna(subset=['timestamp'])
    data['JFT_corrige'] = pd.to_numeric(data['JFT_corrige'], errors='coerce')
    dfs_jft.append(data)
df_jft = pd.concat(dfs_jft).sort_values('timestamp').reset_index(drop=True)

# Fusionner avec dataset principal
df = df.merge(df_jft, left_on='Timestamp', right_on='timestamp', how='left')

# Mettre a jour le debit total
df['JFT_corrige'] = df['JFT_corrige'].fillna(0)
df['Débit total (t/h)'] = df['Débit total (t/h)'] + df['JFT_corrige']

# Supprimer colonnes temporaires
df = df.drop(columns=['timestamp', 'JFT_corrige'], errors='ignore')

print(f"Dataset avec JFT integre : {len(df)} lignes")
print(f"Debit moyen apres correction : {df['Débit total (t/h)'].mean():.2f} t/h")
# 2. Features et cible
features = [
    "Heure (0-23)",
    "Jour semaine (0-6)",
    "Mois (1-12)",
    "Jour mois",
    "Weekend (0/1)",
    "Heure sin",
    "Heure cos",
    "Lag 1h (t/h)",
    "Lag 2h (t/h)",
    "Lag 3h (t/h)",
    "Lag 6h (t/h)",
    "Lag 12h (t/h)",
    "Lag 24h (t/h)",
    "Rolling 3h (t/h)",
    "Rolling 6h (t/h)",
    "Rolling 12h (t/h)",
    "Rolling 24h (t/h)",
    "Std 6h (t/h)",
    "Vente/heure (TSM)",
    "débit_lag_48h",
    "débit_lag_168h",
    "diff_1h",
    "diff_24h"
]
target = "Débit total (t/h)"

X = df[features]
y = df[target]

split = int(len(df) * 0.8)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

print("Dataset charge :", len(df), "lignes")
print("Train:", len(X_train), "| Test:", len(X_test))

# 3. Entrainement avec MLflow
mlflow.set_experiment("OCP_Pipeline_Débit")

with mlflow.start_run(run_name="XGBoost_v3"):

    params = {
        "learning_rate"   : 0.01,
        "max_depth"       : 4,
        "n_estimators"    : 1000,
        "subsample"       : 0.7,
        "colsample_bytree": 0.8,
        "min_child_weight": 5,
        "gamma"           : 0.1,
        "reg_alpha"       : 0.1,
        "reg_lambda"      : 1.5,
    }

    mlflow.log_params(params)

    model = XGBRegressor(
        **params,
        random_state=42,
        early_stopping_rounds=50
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    y_pred = model.predict(X_test)
    r2   = r2_score(y_test, y_pred)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    mlflow.log_metric("R2",   r2)
    mlflow.log_metric("MAE",  mae)
    mlflow.log_metric("RMSE", rmse)

    model.save_model("Data/model_xgboost_ocp_v3.json")
    mlflow.log_artifact("Data/model_xgboost_ocp_v3.json")

    print("=" * 45)
    print("  RESULTATS XGBoost OCP Pipeline")
    print("=" * 45)
    print("  R2   :", round(r2, 4))
    print("  MAE  :", round(mae, 2), "t/h")
    print("  RMSE :", round(rmse, 2), "t/h")
    print("=" * 45)
    print("Experience enregistree dans MLflow !")
