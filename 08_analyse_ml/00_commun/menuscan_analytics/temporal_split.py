"""temporal_split.py : découpage apprentissage / test.

Règle : on évalue un modèle sur des données qu'il n'a jamais vues et qui ressemblent à l'usage réel.
Pour des données datées : apprendre sur le passé, tester sur la période la plus récente.

Pour MenuScan (jalon J8, AUC mesurée sur 2026) :
    apprentissage = lignes dont la résiliation éventuelle prend effet en 2024 ou 2025
    test          = lignes dont la résiliation éventuelle prend effet en 2026
La cible d'une ligne du mois m porte sur le mois m + 1 : la ligne de décembre 2025 appartient donc au test.
"""
from __future__ import annotations

import pandas as pd

DEBUT_DONNEES = pd.Timestamp("2024-01-01")
FIN_DONNEES = pd.Timestamp("2026-12-31")
DERNIER_MOIS_PANEL = pd.Timestamp("2026-11-01")   # sa cible porte sur décembre 2026
DEBUT_TEST = pd.Timestamp("2025-12-01")            # premier mois dont la cible tombe en 2026

APPRENTISSAGE = "entraînement (résiliations 2024-2025)"
TEST = "test (résiliations 2026)"


def jeu(mois: pd.Series) -> pd.Series:
    """Renvoie le libellé du jeu (apprentissage ou test) pour chaque mois d'observation."""
    return pd.Series([TEST if m >= DEBUT_TEST else APPRENTISSAGE for m in mois], index=mois.index)
