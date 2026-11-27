import pandas as pd

from menuscan_analytics.features import _glissant


def _base():
    return pd.DataFrame({"etablissement_id": ["E1", "E1"],
                         "mois": pd.to_datetime(["2025-03-01", "2025-06-01"])})


def _agr():
    mois = pd.date_range("2025-01-01", "2025-06-01", freq="MS")
    return pd.DataFrame({"etablissement_id": "E1", "mois": mois, "sessions": [1, 2, 3, 4, 5, 6]})


def test_somme_glissante_3_mois():
    r = _glissant(_base(), _agr(), ["sessions"], 3, "3m")
    assert list(r["sessions_3m"]) == [1 + 2 + 3, 4 + 5 + 6]


def test_fenetre_precedente_sans_fuite():
    """La fenêtre « 3 mois avant » s'arrête 3 mois avant le mois observé."""
    r = _glissant(_base(), _agr(), ["sessions"], 3, "3m_avant", decalage=3)
    assert list(r["sessions_3m_avant"]) == [0, 1 + 2 + 3]


def test_mois_sans_activite_vaut_zero():
    agr = _agr()[_agr().mois != "2025-06-01"]
    r = _glissant(_base(), agr, ["sessions"], 1, "1m")
    assert list(r["sessions_1m"]) == [3, 0]
