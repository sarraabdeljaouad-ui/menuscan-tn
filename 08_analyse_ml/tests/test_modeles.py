import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from menuscan_analytics import modeles


def _jeu(n=300, graine=0):
    rng = np.random.default_rng(graine)
    df = pd.DataFrame({c: rng.normal(size=n) for c in modeles.NUM})
    for c in modeles.CAT:
        df[c] = rng.choice(["a", "b", "c"], size=n)
    y = (df["tickets_3m"] + rng.normal(size=n) > 1).astype(int)
    return df, y


def _pipeline(df, y):
    pre = ColumnTransformer([("n", StandardScaler(), modeles.NUM),
                             ("c", OneHotEncoder(sparse_output=False), modeles.CAT)])
    return Pipeline([("pre", pre), ("modele", LogisticRegression(max_iter=2000))]).fit(df, y)


def test_contributions_somment_a_l_ecart_de_logit():
    """Somme des facteurs = logit de la ligne - logit de l'établissement moyen de la référence."""
    df, y = _jeu()
    m = _pipeline(df, y)
    contrib = modeles.contributions_logistique(m, df.head(20), df)
    Z = m[0].transform(df)
    logit = m.decision_function(df.head(20))
    logit_moyen = float(Z.mean(axis=0) @ m[-1].coef_[0] + m[-1].intercept_[0])
    assert np.allclose(contrib.sum(axis=1).values, logit - logit_moyen)


def test_chaque_variable_dans_un_seul_facteur():
    toutes = [v for vs in modeles.FACTEURS.values() for v in vs]
    assert sorted(toutes) == sorted(modeles.NUM + modeles.CAT)


def test_trois_facteurs_positifs_seulement():
    contrib = pd.DataFrame({"A": [0.5, -1.0], "B": [0.2, -0.1], "C": [-0.3, 0.4], "D": [0.9, -0.2]})
    r = modeles.trois_facteurs(contrib)
    assert list(r.iloc[0]) == ["D", "A", "B"]
    assert r.iloc[1, 0] == "C" and r.iloc[1, 1:].isna().all()


def test_preparer_echeance_annuelle():
    df = pd.DataFrame({"tendance_usage": [1.0] * 3, "taux_commande_3m": [np.nan, 0.5, 0.2],
                       "tickets_3m": [0, 2, 1], "satisfaction_6m": [np.nan, 4.0, 3.0],
                       "factures_retard_6m": [0, 1, 0], "periodicite_facturation": ["annuelle", "annuelle", "mensuelle"],
                       "anciennete_mois": [11, 10, 11]})
    d = modeles.preparer(df, note_par_defaut=3.9)
    assert list(d["echeance_annuelle"]) == [1, 0, 0]
    assert list(d["sans_commande_table"]) == [1, 0, 0] and d["taux_commande_3m"].iloc[0] == 0
    assert d["satisfaction_6m"].iloc[0] == 3.9 and list(d["tickets_2_ou_plus"]) == [0, 1, 0]
