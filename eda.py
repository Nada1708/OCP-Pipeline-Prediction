"""Figures d'exploration des donnees (rapport, chapitre II).

    py -3.12 eda.py

Produit reports/eda/*.png et reports/eda/stats.json a partir de la serie nettoyee.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ocp_ml import config as C
from ocp_ml.data import charger_serie_horaire

VERT, VERT_CLAIR, AMBRE, BLEU = "#00843D", "#9fd3b4", "#d97706", "#2563eb"
CLIENTS = ["IMACID", "JFO", "JFD", "JFT", "JFQ", "JFF", "PMP"]
SEUIL_MARCHE = 100  # t/h : un client est considere en marche au-dessus
JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]


def sauver(nom):
    plt.tight_layout()
    plt.savefig(DOSSIER / nom, dpi=150, bbox_inches="tight")
    plt.close()


DOSSIER = C.REPORTS_DIR / "eda"


def main():
    DOSSIER.mkdir(parents=True, exist_ok=True)
    df = charger_serie_horaire()
    y = df[C.CIBLE]
    valide = y[y >= C.SEUIL_ARRET]

    # 1. Serie horaire + moyenne journaliere
    plt.figure(figsize=(14, 4.5))
    plt.plot(y.index, y, color=VERT_CLAIR, linewidth=0.6, label="Débit horaire")
    plt.plot(y.resample("D").mean(), color=VERT, linewidth=1.6, label="Moyenne journalière")
    plt.axhline(C.SEUIL_ARRET, color=AMBRE, linestyle="--", linewidth=1, label=f"Seuil d'arrêt ({C.SEUIL_ARRET} t/h)")
    plt.ylabel("Débit total (t/h)")
    plt.title("Débit total distribué — mai à décembre 2024")
    plt.legend(loc="lower left")
    plt.grid(True, alpha=0.3)
    sauver("eda_debit_horaire.png")

    # 2. Distribution par heure (boites a moustaches)
    plt.figure(figsize=(12, 4.5))
    groupes = [valide[valide.index.hour == h].values for h in range(24)]
    plt.boxplot(groupes, tick_labels=[f"{h}h" for h in range(24)], showfliers=False,
                patch_artist=True, boxprops={"facecolor": VERT_CLAIR, "color": VERT},
                medianprops={"color": VERT, "linewidth": 2})
    plt.plot(range(1, 25), [g.mean() for g in groupes], "o-", color=AMBRE, markersize=4, label="Moyenne")
    plt.ylabel("Débit total (t/h)")
    plt.title("Débit selon l'heure de la journée (hors arrêts)")
    plt.legend()
    plt.grid(True, axis="y", alpha=0.3)
    sauver("eda_profil_heure.png")

    # 3. Carte de chaleur jour x heure
    profil = valide.groupby([valide.index.dayofweek, valide.index.hour]).mean().unstack()
    plt.figure(figsize=(12, 3.8))
    plt.imshow(profil.values, aspect="auto", cmap="Greens")
    plt.colorbar(label="Débit moyen (t/h)")
    plt.yticks(range(7), JOURS)
    plt.xticks(range(0, 24, 2), [f"{h}h" for h in range(0, 24, 2)])
    plt.title("Débit moyen selon le jour de la semaine et l'heure")
    sauver("eda_profil_semaine.png")

    # 4. Clients : debit moyen et regime marche / arret
    marche = pd.DataFrame({c: (df[c] > SEUIL_MARCHE) for c in CLIENTS})
    changements = marche.astype(int).diff().abs().sum() / (len(df) / 24)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
    moyennes = df[CLIENTS].where(marche).mean()
    axes[0].bar(CLIENTS, moyennes, color=VERT)
    axes[0].set_ylabel("t/h")
    axes[0].set_title("Débit moyen de chaque client lorsqu'il est en marche")
    axes[0].grid(True, axis="y", alpha=0.3)
    axes[1].bar(CLIENTS, changements, color=AMBRE)
    axes[1].set_ylabel("Changements d'état par jour")
    axes[1].set_title("Fréquence des démarrages / arrêts")
    axes[1].grid(True, axis="y", alpha=0.3)
    sauver("eda_clients.png")

    # 5. Autocorrelation
    decalages = np.arange(1, 169)
    acf = [y.autocorr(k) for k in decalages]
    plt.figure(figsize=(12, 4))
    plt.bar(decalages, acf, color=VERT, width=0.8)
    for k in (1, 6, 24, 168):
        plt.annotate(f"{acf[k - 1]:.2f}", (k, acf[k - 1]), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=9)
    plt.xlabel("Décalage (heures)")
    plt.ylabel("Autocorrélation")
    plt.title("Autocorrélation du débit total : la mémoire de la série s'estompe en quelques heures")
    plt.grid(True, axis="y", alpha=0.3)
    sauver("eda_autocorrelation.png")

    stats = {
        "heures": int(len(df)),
        "heures_valides": int(y.notna().sum()),
        "heures_hors_arret": int(len(valide)),
        "moyenne": round(float(valide.mean()), 1),
        "ecart_type": round(float(valide.std()), 1),
        "min": round(float(valide.min()), 1),
        "max": round(float(valide.max()), 1),
        "heure_max": int(profil.mean().idxmax()),
        "heure_min": int(profil.mean().idxmin()),
        "moyenne_semaine": round(float(valide[valide.index.dayofweek < 5].mean()), 1),
        "moyenne_weekend": round(float(valide[valide.index.dayofweek >= 5].mean()), 1),
        "autocorrelation": {str(k): round(float(acf[k - 1]), 3) for k in (1, 2, 3, 6, 12, 24, 48, 168)},
        "clients": {c: {"debit_moyen_en_marche": round(float(moyennes[c]), 1),
                        "part_en_marche": round(float(marche[c].mean()), 3),
                        "changements_par_jour": round(float(changements[c]), 2)} for c in CLIENTS},
        "moyenne_mensuelle": {str(m): round(float(v), 1) for m, v in valide.groupby(valide.index.month).mean().items()},
    }
    with open(DOSSIER / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
