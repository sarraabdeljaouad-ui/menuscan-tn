"""data_mining.py : associations entre plats (EF-12) et sensibilité des ventes au prix (EF-11).

Deux méthodes, toutes deux construites pour neutraliser l'effet « établissement » :
- lift ajusté : chaque établissement a sa carte et sa clientèle. On compare les paniers d'un établissement
  à ce qu'on attendrait dans CE établissement, puis on additionne sur les établissements ;
- élasticité : régression de Poisson conditionnelle. Les ventes d'un article sont comparées aux autres
  articles de la même catégorie, du même établissement, le même mois (effet fixe « cellule »), et à
  lui-même avant et après son changement de prix (effet fixe « article »).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.optimize import minimize
from scipy.stats import poisson


# ---------------------------------------------------------------------------------------------------------------
# Associations
# ---------------------------------------------------------------------------------------------------------------
def cooccurrences(lignes: pd.DataFrame, colonne: str) -> tuple[list, np.ndarray, np.ndarray, np.ndarray]:
    """Compte, pour chaque paire (a, b) d'éléments (plats ou catégories) :
    - observe[a, b] : commandes contenant a et b ;
    - attendu[a, b] : somme sur les établissements de n_e(a) x n_e(b) / N_e (indépendance dans l'établissement) ;
    - avec_a[a, b] : commandes contenant a, dans les établissements qui proposent b (dénominateur de la confiance).

    lignes : une ligne par article de commande, colonnes etablissement_id, commande_id et `colonne`.
    """
    elements = sorted(lignes[colonne].unique())
    ix = {v: i for i, v in enumerate(elements)}
    k = len(elements)
    observe, attendu, avec_a = np.zeros((k, k)), np.zeros((k, k)), np.zeros((k, k))
    for _, g in lignes.groupby("etablissement_id"):
        m = pd.crosstab(g["commande_id"], g[colonne]).gt(0).astype(float)
        cols = [ix[c] for c in m.columns]
        M = m.values
        n, N = M.sum(axis=0), len(M)
        bloc = np.ix_(cols, cols)
        observe[bloc] += M.T @ M
        attendu[bloc] += np.outer(n, n) / N
        avec_a[bloc] += np.repeat(n[:, None], len(cols), axis=1)
    return elements, observe, attendu, avec_a


def regles(lignes: pd.DataFrame, colonne: str, lift_min: float = 1.2, alpha: float = 0.05) -> pd.DataFrame:
    """Toutes les paires a -> b avec leur lift ajusté, leur confiance et un test de Poisson unilatéral.

    `retenue` = lift ajusté >= lift_min ET p-value < alpha / nombre de paires testées (correction de Bonferroni :
    avec des milliers de paires, quelques-unes sortiraient par hasard sans cette correction).
    """
    elements, obs, att, avec_a = cooccurrences(lignes, colonne)
    i, j = np.where(~np.eye(len(elements), dtype=bool) & (att > 0))
    r = pd.DataFrame({"antecedent": np.array(elements)[i], "consequent": np.array(elements)[j],
                      "commandes_ensemble": obs[i, j], "attendu": att[i, j],
                      "confiance": obs[i, j] / avec_a[i, j]})
    r["lift_ajuste"] = r["commandes_ensemble"] / r["attendu"]
    r["p_value"] = poisson.sf(r["commandes_ensemble"] - 1, r["attendu"])
    nb_tests = len(r) / 2                                       # chaque paire apparaît dans les deux sens
    r["retenue"] = (r["lift_ajuste"] >= lift_min) & (r["p_value"] < alpha / nb_tests)
    return r.sort_values("lift_ajuste", ascending=False).reset_index(drop=True)


def lift_sur(lignes: pd.DataFrame, colonne: str, paires: pd.DataFrame) -> pd.Series:
    """Lift ajusté des paires (antecedent, consequent) recalculé sur un autre jeu de lignes (ex. 2026)."""
    elements, obs, att, _ = cooccurrences(lignes, colonne)
    ix = {v: i for i, v in enumerate(elements)}
    valeurs = []
    for a, b in zip(paires["antecedent"], paires["consequent"]):
        if a in ix and b in ix and att[ix[a], ix[b]] > 0:
            valeurs.append(obs[ix[a], ix[b]] / att[ix[a], ix[b]])
        else:
            valeurs.append(np.nan)
    return pd.Series(valeurs, index=paires.index)


# ---------------------------------------------------------------------------------------------------------------
# Sensibilité au prix
# ---------------------------------------------------------------------------------------------------------------
def elasticite(panel: pd.DataFrame) -> tuple[float, int]:
    """Élasticité-prix par régression de Poisson conditionnelle (effets fixes « cellule » et « article »).

    panel : une ligne par article proposé et par mois, colonnes article_id, cellule (établissement x catégorie x mois),
    prix_ttc (prix en vigueur) et q (quantité vendue, zéros compris).

    Modèle : E[q] = exp(cellule + article + e x log(prix)). L'effet cellule est éliminé analytiquement (vraisemblance
    multinomiale dans chaque cellule). Les articles dont le prix a changé apportent l'information sur e ; les autres
    articles de la même cellule servent de témoins. Renvoie (e, nombre d'articles dont le prix a changé).
    """
    # Les articles au prix constant restent : ils servent de témoins dans leur cellule. Seuls les articles jamais
    # vendus sont retirés (leur effet fixe partirait vers moins l'infini).
    d = panel[panel.groupby("article_id")["q"].transform("sum") > 0]
    # Un article seul dans sa cellule n'apporte rien : on retire ces lignes (peut en créer d'autres, d'où la boucle)
    while True:
        garde = d.groupby("cellule")["article_id"].transform("size") > 1
        if garde.all():
            break
        d = d[garde]
    informatifs = int(d.loc[d.groupby("article_id")["prix_ttc"].transform("nunique") > 1, "article_id"].nunique())
    if d.empty or informatifs == 0:
        return float("nan"), 0
    art = pd.factorize(d["article_id"])[0]
    n, k = len(d), art.max() + 1
    A = sp.csr_matrix((np.ones(n), (np.arange(n), art)), shape=(n, k))[:, 1:]
    lp, y = np.log(d["prix_ttc"].to_numpy(float)), d["q"].to_numpy(float)
    cel = pd.factorize(d["cellule"])[0]
    Q = np.bincount(cel, weights=y)

    def moins_vraisemblance(b):
        xb = lp * b[0] + A @ b[1:]
        m = xb.max()
        e = np.exp(xb - m)
        s = np.bincount(cel, weights=e)
        ll = (y * xb).sum() - (Q * (np.log(s) + m)).sum()
        r = y - Q[cel] * e / s[cel]
        return -ll, -np.concatenate([[lp @ r], A.T @ r])

    res = minimize(moins_vraisemblance, np.zeros(k), jac=True, method="L-BFGS-B", options={"maxiter": 3000})
    return float(res.x[0]), informatifs


def elasticite_bootstrap(panel: pd.DataFrame, n: int = 200, graine: int = 42) -> tuple[float, float, float, int]:
    """Élasticité et intervalle à 95 % par bootstrap par établissement. Renvoie (e, bas, haut, articles)."""
    e, nb = elasticite(panel)
    groupes = {k: g for k, g in panel.groupby("etablissement_id")}
    cles = list(groupes)
    rng = np.random.default_rng(graine)
    tirages = []
    for _ in range(n):
        parts = []
        for i, c in enumerate(rng.choice(cles, size=len(cles), replace=True)):
            g = groupes[c]
            parts.append(g.assign(cellule=g["cellule"] + f"#{i}", article_id=g["article_id"] + f"#{i}"))
        tirages.append(elasticite(pd.concat(parts, ignore_index=True))[0])
    bas, haut = np.nanpercentile(tirages, [2.5, 97.5])
    return e, float(bas), float(haut), nb
