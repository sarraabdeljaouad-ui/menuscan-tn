"""config.py : réglages communs de l'analyse (dossiers, dates, affichage).

Si un dossier ou une couleur change, on le change ici et tous les notebooks suivent.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# 1. Dossiers
RACINE = Path(__file__).resolve().parents[2]          # 08_analyse_ml/
DEPOT = RACINE.parent                                 # racine du dépôt menuscan-tn
DOSSIER_FEATURES = RACINE / "05_data" / "features"
DOSSIER_METADATA = RACINE / "05_data" / "metadata"
DOSSIER_FIGURES = RACINE / "06_exports" / "figures"
DOSSIER_TABLES = RACINE / "06_exports" / "tables"
DOSSIER_MODELES = RACINE / "06_exports" / "modeles"
DOSSIER_PREDICTIONS = RACINE / "06_exports" / "predictions"
DOSSIER_JOURNAUX = RACINE / "06_exports" / "journaux"
DOSSIER_LIVRABLES = RACINE / "04_livrables"

# Suivi des essais MLflow, en local (base SQLite et fichiers dans 06_exports/journaux, hors Git)
MLFLOW_URI = "sqlite:///" + (DOSSIER_JOURNAUX / "mlflow.db").as_posix()
MLFLOW_ARTEFACTS = (DOSSIER_JOURNAUX / "mlartefacts").as_uri()

# 2. Données
SCHEMA_MARTS = "marts"        # entrepôt construit par dbt (phase 4)
SCHEMA_RESULTATS = "ml"       # résultats publiés pour Power BI (T7.4)
DATE_ARRETE = pd.Timestamp("2026-12-31")

# 3. Affichage
BLEU, ORANGE, GRIS = "#1D4ED8", "#C2410C", "#94A3B8"


def experience_mlflow(nom: str) -> None:
    """Active le suivi MLflow local et l'expérience demandée (créée au premier appel)."""
    import mlflow
    DOSSIER_JOURNAUX.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(MLFLOW_URI)
    if mlflow.get_experiment_by_name(nom) is None:
        mlflow.create_experiment(nom, artifact_location=MLFLOW_ARTEFACTS)
    mlflow.set_experiment(nom)


def style():
    """Style commun des graphiques et des tableaux."""
    pd.set_option("display.float_format", lambda v: f"{v:,.3f}".replace(",", " "))
    plt.rcParams.update({"figure.figsize": (9, 3.6), "axes.spines.top": False, "axes.spines.right": False})


def enregistrer_figure(fig, nom: str) -> Path:
    """Enregistre une figure en PNG dans 06_exports/figures (nom sans extension)."""
    DOSSIER_FIGURES.mkdir(parents=True, exist_ok=True)
    chemin = DOSSIER_FIGURES / f"{nom}.png"
    fig.savefig(chemin, dpi=120, bbox_inches="tight")
    return chemin


def enregistrer_table(df: pd.DataFrame, nom: str, index: bool = True) -> Path:
    """Enregistre un tableau en CSV (UTF-8, séparateur ;) dans 06_exports/tables."""
    DOSSIER_TABLES.mkdir(parents=True, exist_ok=True)
    chemin = DOSSIER_TABLES / f"{nom}.csv"
    df.to_csv(chemin, sep=";", index=index, encoding="utf-8-sig")
    return chemin
