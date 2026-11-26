"""Outils communs aux scripts de la démonstration mensuelle (phase 5, T5.2)."""
import os
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "04_ingestion"))
from ingerer import SOURCES, lire_env  # noqa: E402

BRUTES = RACINE / "menuscan_dataset" / "donnees_brutes"
ARRIVEES = RACINE / "menuscan_dataset" / "demo_arrivees"     # fichiers « livrés » au fil des mois
BASE_DEMO = "menuscan_demo"
MOIS = [f"{a}-{m:02d}" for a in (2024, 2025, 2026) for m in range(1, 13)]


def connexion(base):
    import psycopg2
    env = lire_env()
    return psycopg2.connect(host=env.get("POSTGRES_HOST", "127.0.0.1"), port=env.get("POSTGRES_PORT", "5440"),
                            user=env["POSTGRES_USER"], password=env["POSTGRES_PASSWORD"], dbname=base, connect_timeout=10)
