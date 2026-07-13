import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from xgboost import XGBRegressor
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ============================================
# CONFIGURATION
# ============================================
st.set_page_config(
    page_title="OCP Pipeline | Prediction Debit",
    page_icon="assets/ocp_logo.png" if True else "🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# STYLE CSS
# ============================================
st.markdown("""
<style>
    /* Couleurs OCP */
    :root {
        --ocp-green: #00843D;
        --ocp-dark: #1a1a2e;
        --ocp-gray: #f5f5f5;
    }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #00843D, #005a2b);
        padding: 20px 30px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
    }

    /* KPI Cards */
    .kpi-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00843D;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        color: #00843D;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 5px;
    }

    /* Prediction card */
    .prediction-card {
        background: linear-gradient(135deg, #00843D, #005a2b);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin: 20px 0;
    }
    .prediction-value {
        font-size: 3rem;
        font-weight: bold;
    }

    /* Sidebar */
    .css-1d391kg {
        background: #1a1a2e;
    }

    /* Badges */
    .badge-success {
        background: #00843D;
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
    }
    .badge-warning {
        background: #FFC107;
        color: black;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
    }

    /* Section titles */
    .section-title {
        color: #00843D;
        font-size: 1.3rem;
        font-weight: bold;
        border-bottom: 2px solid #00843D;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CHARGEMENT DES DONNEES ET MODELE
# ============================================
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("Data/OCP_Dataset_ML.xlsx", header=2)
        df["debit_lag_48h"]  = df["Debit total (t/h)"].shift(48)
        df["debit_lag_168h"] = df["Debit total (t/h)"].shift(168)
        df["diff_1h"]        = df["Debit total (t/h)"].diff(1)
        df["diff_24h"]       = df["Debit total (t/h)"].diff(24)
        df = df.dropna().reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Erreur chargement donnees: {e}")
        return None

@st.cache_resource
def load_model():
    try:
        model = XGBRegressor()
        model.load_model("Data/model_xgboost_ocp_v3.json")
        return model
    except Exception as e:
        st.warning(f"Modele non trouve, rechargement en cours...")
        return None

# ============================================
# SIDEBAR NAVIGATION
# ============================================
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 10px;'>
        <h2 style='color: #00843D;'>🏭 OCP Pipeline</h2>
        <p style='color: #888; font-size: 0.8rem;'>Systeme de Prediction de Debit</p>
        <hr style='border-color: #333;'>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["🏠 Accueil", "📊 Dashboard", "🔮 Prediction", "📈 Performances", "ℹ️ A propos"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("""
    <div style='padding: 10px; background: #f0f0f0; border-radius: 8px; font-size: 0.8rem;'>
        <b>Statut Pipeline</b><br>
        <span style='color: green;'>● En ligne</span><br><br>
        <b>Modele</b>: XGBoost v3<br>
        <b>R²</b>: 0.96<br>
        <b>MAE</b>: 14.96 t/h<br>
        <b>Derniere MAJ</b>: {date}
    </div>
    """.format(date=datetime.now().strftime("%d/%m/%Y")), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style='text-align:center; font-size: 0.75rem; color: #888;'>
        Stagiaire : Nada Elaali<br>
        Superviseur : M. Salama<br>
        OCP Jorf Lasfar 2025
    </div>
    """, unsafe_allow_html=True)

# ============================================
# PAGE : ACCUEIL
# ============================================
if page == "🏠 Accueil":

    st.markdown("""
    <div class='main-header'>
        <h1>🏭 OCP — Prediction du Debit Horaire</h1>
        <p>Pipeline Khouribga → Jorf Lasfar | Systeme MLOps</p>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class='kpi-card'>
            <div class='kpi-value'>0.96</div>
            <div class='kpi-label'>R² du modele</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='kpi-card'>
            <div class='kpi-value'>14.96</div>
            <div class='kpi-label'>MAE (t/h)</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='kpi-card'>
            <div class='kpi-value'>5 393</div>
            <div class='kpi-label'>Donnees d'entrainement</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class='kpi-card'>
            <div class='kpi-value'>8 mois</div>
            <div class='kpi-label'>Historique (Mai-Dec 2024)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Pipeline CRISP-DM
    st.markdown("<div class='section-title'>📋 Methodologie CRISP-DM</div>", unsafe_allow_html=True)

    etapes = {
        "Business Understanding": ("✅", "Prediction debit horaire pipeline"),
        "Data Understanding": ("✅", "2 fichiers sources, 5 967 mesures horaires"),
        "Data Preparation": ("✅", "Nettoyage, fusion, feature engineering"),
        "Modeling": ("✅", "XGBoost R2=0.96, MAE=14.96 t/h"),
        "Evaluation": ("✅", "Validation temporelle, sans data leakage"),
        "Deployment": ("🔄", "Streamlit + MLflow (en cours)")
    }

    cols = st.columns(6)
    for i, (etape, (status, desc)) in enumerate(etapes.items()):
        with cols[i]:
            color = "#00843D" if status == "✅" else "#FFC107"
            st.markdown(f"""
            <div style='text-align:center; padding:10px; background:white;
                        border-radius:8px; border-top: 4px solid {color};
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1); height: 120px;'>
                <div style='font-size:1.5rem;'>{status}</div>
                <div style='font-size:0.75rem; font-weight:bold; color:{color};'>{etape}</div>
                <div style='font-size:0.65rem; color:#888; margin-top:5px;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Description
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='section-title'>🎯 Objectif</div>", unsafe_allow_html=True)
        st.info("""
        Predire le debit horaire (t/h) necessaire a envoyer depuis Khouribga
        vers les clients de Jorf Lasfar, en tenant compte de l'heure de la journee
        et de l'historique des capteurs du pipeline.
        """)

    with col2:
        st.markdown("<div class='section-title'>🛠️ Technologies</div>", unsafe_allow_html=True)
        tech_cols = st.columns(3)
        techs = ["Python", "XGBoost", "MLflow", "Streamlit", "Pandas", "Plotly"]
        for i, tech in enumerate(techs):
            with tech_cols[i % 3]:
                st.markdown(f"""
                <div style='text-align:center; background:#f0f9f4; padding:8px;
                            border-radius:8px; margin:3px; font-size:0.8rem;
                            border: 1px solid #00843D; color:#00843D; font-weight:bold;'>
                    {tech}
                </div>
                """, unsafe_allow_html=True)

# ============================================
# PAGE : DASHBOARD
# ============================================
elif page == "📊 Dashboard":

    st.markdown("<h2 style='color:#00843D;'>📊 Dashboard — Analyse des donnees</h2>", unsafe_allow_html=True)

    df = load_data()
    if df is not None:

        # Statistiques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Debit moyen", f"{df['Debit total (t/h)'].mean():.0f} t/h")
        with col2:
            st.metric("Debit max", f"{df['Debit total (t/h)'].max():.0f} t/h")
        with col3:
            st.metric("Debit min", f"{df['Debit total (t/h)'].min():.0f} t/h")

        st.markdown("---")

        # Graphe 1 : Serie temporelle
        st.markdown("<div class='section-title'>📈 Evolution du debit horaire</div>", unsafe_allow_html=True)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df["Timestamp"], y=df["Debit total (t/h)"],
            mode='lines', name='Debit total (t/h)',
            line=dict(color='#00843D', width=1)
        ))
        fig1.update_layout(
            title="Debit horaire — Mai a Decembre 2024",
            xaxis_title="Date",
            yaxis_title="Debit (t/h)",
            template="plotly_white",
            height=350
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Graphe 2 : Distribution par heure
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='section-title'>🕐 Debit moyen par heure</div>", unsafe_allow_html=True)
            debit_heure = df.groupby("Heure (0-23)")["Debit total (t/h)"].mean().reset_index()
            fig2 = px.bar(debit_heure, x="Heure (0-23)", y="Debit total (t/h)",
                         color="Debit total (t/h)", color_continuous_scale="Greens",
                         title="Debit moyen par heure de la journee")
            fig2.update_layout(template="plotly_white", height=300)
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            st.markdown("<div class='section-title'>📅 Debit moyen par jour</div>", unsafe_allow_html=True)
            jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
            debit_jour = df.groupby("Jour semaine (0-6)")["Debit total (t/h)"].mean().reset_index()
            debit_jour["Jour"] = debit_jour["Jour semaine (0-6)"].map(dict(enumerate(jours)))
            fig3 = px.bar(debit_jour, x="Jour", y="Debit total (t/h)",
                         color="Debit total (t/h)", color_continuous_scale="Greens",
                         title="Debit moyen par jour de la semaine")
            fig3.update_layout(template="plotly_white", height=300)
            st.plotly_chart(fig3, use_container_width=True)

# ============================================
# PAGE : PREDICTION
# ============================================
elif page == "🔮 Prediction":

    st.markdown("<h2 style='color:#00843D;'>🔮 Prediction du Debit Horaire</h2>", unsafe_allow_html=True)

    model = load_model()
    df = load_data()

    if model is None:
        st.error("Modele non disponible. Verifiez que model_xgboost_ocp_v3.json est dans le dossier Data/")
    else:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("<div class='section-title'>⚙️ Parametres d'entree</div>", unsafe_allow_html=True)

            with st.form("prediction_form"):

                st.markdown("**Variables temporelles**")
                c1, c2 = st.columns(2)
                with c1:
                    heure = st.slider("Heure (0-23)", 0, 23, 8)
                    mois = st.slider("Mois (1-12)", 1, 12, 6)
                with c2:
                    jour_semaine = st.selectbox("Jour de la semaine",
                        ["Lundi (0)", "Mardi (1)", "Mercredi (2)", "Jeudi (3)",
                         "Vendredi (4)", "Samedi (5)", "Dimanche (6)"])
                    jour_mois = st.slider("Jour du mois", 1, 31, 15)

                est_weekend = 1 if jour_semaine in ["Samedi (5)", "Dimanche (6)"] else 0

                st.markdown("**Historique du debit (t/h)**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    lag_1h = st.number_input("Debit il y a 1h", value=1500.0, step=10.0)
                    lag_2h = st.number_input("Debit il y a 2h", value=1480.0, step=10.0)
                with c2:
                    lag_3h = st.number_input("Debit il y a 3h", value=1460.0, step=10.0)
                    lag_6h = st.number_input("Debit il y a 6h", value=1450.0, step=10.0)
                with c3:
                    lag_12h = st.number_input("Debit il y a 12h", value=1440.0, step=10.0)
                    lag_24h = st.number_input("Debit il y a 24h", value=1500.0, step=10.0)

                st.markdown("**Moyennes mobiles et tendances**")
                c1, c2 = st.columns(2)
                with c1:
                    rolling_3h  = st.number_input("Moyenne 3h", value=1480.0, step=10.0)
                    rolling_6h  = st.number_input("Moyenne 6h", value=1470.0, step=10.0)
                    rolling_12h = st.number_input("Moyenne 12h", value=1460.0, step=10.0)
                    rolling_24h = st.number_input("Moyenne 24h", value=1450.0, step=10.0)
                with c2:
                    std_6h      = st.number_input("Ecart-type 6h", value=30.0, step=5.0)
                    vente_heure = st.number_input("Vente/heure (TSM)", value=2500.0, step=50.0)
                    lag_48h     = st.number_input("Debit il y a 48h", value=1490.0, step=10.0)
                    lag_168h    = st.number_input("Debit il y a 168h", value=1500.0, step=10.0)

                st.markdown("**Variations**")
                c1, c2 = st.columns(2)
                with c1:
                    diff_1h  = st.number_input("Variation 1h", value=20.0, step=5.0)
                with c2:
                    diff_24h_val = st.number_input("Variation 24h", value=0.0, step=5.0)

                predict_btn = st.form_submit_button("🔮 Predire le debit", use_container_width=True)

        with col2:
            st.markdown("<div class='section-title'>📊 Resultat de la prediction</div>", unsafe_allow_html=True)

            if predict_btn:
                # Encodage cyclique
                heure_sin = np.sin(2 * np.pi * heure / 24)
                heure_cos = np.cos(2 * np.pi * heure / 24)
                jour_num = int(jour_semaine.split("(")[1].replace(")", ""))

                # Vecteur de features
                X_pred = pd.DataFrame([[
                    heure, jour_num, mois, jour_mois, est_weekend,
                    heure_sin, heure_cos,
                    lag_1h, lag_2h, lag_3h, lag_6h, lag_12h, lag_24h,
                    rolling_3h, rolling_6h, rolling_12h, rolling_24h,
                    std_6h, vente_heure, lag_48h, lag_168h, diff_1h, diff_24h_val
                ]], columns=[
                    "Heure (0-23)", "Jour semaine (0-6)", "Mois (1-12)", "Jour mois", "Weekend (0/1)",
                    "Heure sin", "Heure cos",
                    "Lag 1h (t/h)", "Lag 2h (t/h)", "Lag 3h (t/h)",
                    "Lag 6h (t/h)", "Lag 12h (t/h)", "Lag 24h (t/h)",
                    "Rolling 3h (t/h)", "Rolling 6h (t/h)", "Rolling 12h (t/h)", "Rolling 24h (t/h)",
                    "Std 6h (t/h)", "Vente/heure (TSM)",
                    "debit_lag_48h", "debit_lag_168h", "diff_1h", "diff_24h"
                ])

                prediction = model.predict(X_pred)[0]

                # Affichage resultat
                st.markdown(f"""
                <div class='prediction-card'>
                    <div style='font-size:1rem; opacity:0.8;'>Debit predit</div>
                    <div class='prediction-value'>{prediction:.1f}</div>
                    <div style='font-size:1.2rem;'>t/h</div>
                </div>
                """, unsafe_allow_html=True)

                # Indicateur
                if prediction > 1600:
                    st.success("🟢 Debit eleve — Production optimale")
                elif prediction > 1200:
                    st.info("🔵 Debit normal — Production standard")
                else:
                    st.warning("🟡 Debit faible — Verifier le pipeline")

                # Graphe comparatif
                if df is not None:
                    debit_moyen = df["Debit total (t/h)"].mean()
                    fig = go.Figure(go.Bar(
                        x=["Debit predit", "Debit moyen historique"],
                        y=[prediction, debit_moyen],
                        marker_color=["#00843D", "#888"]
                    ))
                    fig.update_layout(
                        title="Comparaison avec la moyenne historique",
                        yaxis_title="Debit (t/h)",
                        template="plotly_white",
                        height=250
                    )
                    st.plotly_chart(fig, use_container_width=True)

            else:
                st.markdown("""
                <div style='text-align:center; padding:50px; color:#888;'>
                    <div style='font-size:3rem;'>🔮</div>
                    <p>Remplissez les parametres et cliquez sur<br><b>Predire le debit</b></p>
                </div>
                """, unsafe_allow_html=True)

# ============================================
# PAGE : PERFORMANCES
# ============================================
elif page == "📈 Performances":

    st.markdown("<h2 style='color:#00843D;'>📈 Performances du modele</h2>", unsafe_allow_html=True)

    df = load_data()
    model = load_model()

    if df is not None and model is not None:

        features = [
            "Heure (0-23)", "Jour semaine (0-6)", "Mois (1-12)", "Jour mois", "Weekend (0/1)",
            "Heure sin", "Heure cos",
            "Lag 1h (t/h)", "Lag 2h (t/h)", "Lag 3h (t/h)",
            "Lag 6h (t/h)", "Lag 12h (t/h)", "Lag 24h (t/h)",
            "Rolling 3h (t/h)", "Rolling 6h (t/h)", "Rolling 12h (t/h)", "Rolling 24h (t/h)",
            "Std 6h (t/h)", "Vente/heure (TSM)",
            "debit_lag_48h", "debit_lag_168h", "diff_1h", "diff_24h"
        ]

        X = df[features]
        y = df["Debit total (t/h)"]
        split = int(len(df) * 0.8)
        X_test = X.iloc[split:]
        y_test = y.iloc[split:]
        y_pred = model.predict(X_test)

        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
        r2   = r2_score(y_test, y_pred)
        mae  = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        # Metriques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("R²", f"{r2:.4f}", delta=f"+{r2-0.70:.2f} vs baseline")
        with col2:
            st.metric("MAE", f"{mae:.2f} t/h", delta=f"-{84.23-mae:.2f} vs baseline")
        with col3:
            st.metric("RMSE", f"{rmse:.2f} t/h", delta=f"-{144.12-rmse:.2f} vs baseline")

        st.markdown("---")

        # Graphe reel vs predit
        st.markdown("<div class='section-title'>📊 Reel vs Predit</div>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=y_test.values[:300], name="Reel",
                                  line=dict(color="#00843D", width=1.5)))
        fig.add_trace(go.Scatter(y=y_pred[:300], name="Predit",
                                  line=dict(color="#FFA500", width=1.5, dash="dash")))
        fig.update_layout(
            title="Debit reel vs predit (300 premieres heures du test)",
            xaxis_title="Heures", yaxis_title="Debit (t/h)",
            template="plotly_white", height=350
        )
        st.plotly_chart(fig, use_container_width=True)

        # Importance des features
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='section-title'>🎯 Importance des variables</div>", unsafe_allow_html=True)
            importances = pd.DataFrame({
                "Feature": features,
                "Importance": model.feature_importances_
            }).sort_values("Importance", ascending=True).tail(10)

            fig2 = px.bar(importances, x="Importance", y="Feature",
                         orientation="h", color="Importance",
                         color_continuous_scale="Greens",
                         title="Top 10 variables les plus importantes")
            fig2.update_layout(template="plotly_white", height=350)
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            st.markdown("<div class='section-title'>📉 Scatter reel vs predit</div>", unsafe_allow_html=True)
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=y_test.values, y=y_pred,
                                       mode="markers", marker=dict(color="#00843D", opacity=0.3, size=4),
                                       name="Predictions"))
            lims = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
            fig3.add_trace(go.Scatter(x=lims, y=lims, mode="lines",
                                       line=dict(color="red", dash="dash"), name="Parfait"))
            fig3.update_layout(
                title="Scatter: Reel vs Predit",
                xaxis_title="Reel (t/h)", yaxis_title="Predit (t/h)",
                template="plotly_white", height=350
            )
            st.plotly_chart(fig3, use_container_width=True)

# ============================================
# PAGE : A PROPOS
# ============================================
elif page == "ℹ️ A propos":

    st.markdown("<h2 style='color:#00843D;'>ℹ️ A propos du projet</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style='background:white; padding:20px; border-radius:10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
            <h3 style='color:#00843D;'>👤 Informations du projet</h3>
            <table style='width:100%;'>
                <tr><td><b>Stagiaire</b></td><td>Nada Elaali</td></tr>
                <tr><td><b>Superviseur</b></td><td>M. Othmane Salama</td></tr>
                <tr><td><b>Entreprise</b></td><td>OCP Group — Jorf Lasfar</td></tr>
                <tr><td><b>Periode</b></td><td>2025</td></tr>
                <tr><td><b>Methode</b></td><td>CRISP-DM + MLOps</td></tr>
                <tr><td><b>Modele</b></td><td>XGBoost</td></tr>
                <tr><td><b>GitHub</b></td><td>github.com/Nada1708/OCP-Pipeline-Prediction</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background:white; padding:20px; border-radius:10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
            <h3 style='color:#00843D;'>📊 Resultats du modele</h3>
            <table style='width:100%;'>
                <tr><td><b>Baseline R²</b></td><td>0.70</td></tr>
                <tr><td><b>Modele final R²</b></td><td><b style='color:#00843D;'>0.96</b></td></tr>
                <tr><td><b>MAE</b></td><td>14.96 t/h</td></tr>
                <tr><td><b>RMSE</b></td><td>53.72 t/h</td></tr>
                <tr><td><b>Donnees</b></td><td>Mai-Dec 2024 (horaire)</td></tr>
                <tr><td><b>Validation</b></td><td>Split temporel 80/20</td></tr>
                <tr><td><b>Data leakage</b></td><td>Verifie et corrige</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)