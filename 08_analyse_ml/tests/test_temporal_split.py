import pandas as pd

from menuscan_analytics import temporal_split as ts


def test_decembre_2025_est_en_test():
    """La cible de décembre 2025 porte sur janvier 2026 : la ligne va dans le test."""
    mois = pd.Series(pd.to_datetime(["2025-11-01", "2025-12-01", "2026-11-01"]))
    assert list(ts.jeu(mois)) == [ts.APPRENTISSAGE, ts.TEST, ts.TEST]


def test_dates_coherentes():
    assert ts.DEBUT_DONNEES < ts.DEBUT_TEST <= ts.DERNIER_MOIS_PANEL < ts.FIN_DONNEES
