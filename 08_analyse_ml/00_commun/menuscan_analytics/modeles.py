"""modeles.py : variables du modèle de résiliation, facteurs par établissement, mesures, registre.

Utilisé par 03_machine_learning/02_prediction_resiliation (K19, EF-10).
"""
from __future__ import annotations

import json
from datetime import date

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from . import config

# Variables numériques et qualitatives du modèle de résiliation
NUM = [
    "sessions_table_jour_1m", "sessions_table_jour_3m", "log_tendance_usage",
    "taux_commande_3m", "sans_commande_table",
    "tickets_3m", "tickets_2_ou_plus", "satisfaction_6m", "sans_note",
    "part_factures_retard_6m", "a_facture_retard_6m",
    "anciennete_mois", "mrr_ht", "nb_tables", "echeance_annuelle", "facturation_mensuelle",
]
CAT = ["formule", "type_etablissement", "region", "type_canal"]

# Regroupement des variables en facteurs lisibles (les 3 principaux sont publiés par établissement)
# Libellés neutres : un facteur cité est un facteur qui augmente le risque de cet établissement ; son sens
# (usage bas, tendance, etc.) se lit dans les variables, pas dans le libellé.
FACTEURS = {
    "Usage du menu": ["sessions_table_jour_1m", "sessions_table_jour_3m", "log_tendance_usage"],
    "Commande à table": ["taux_commande_3m", "sans_commande_table"],
    "Tickets de support": ["tickets_3m", "tickets_2_ou_plus"],
    "Satisfaction support": ["satisfaction_6m", "sans_note"],
    "Retards de paiement": ["part_factures_retard_6m", "a_facture_retard_6m"],
    "Ancienneté": ["anciennete_mois"],
    "Échéance de l'engagement annuel": ["echeance_annuelle"],
    "Facturation mensuelle": ["facturation_mensuelle"],
    "Montant de l'abonnement": ["mrr_ht"],
    "Taille (tables)": ["nb_tables"],
    "Formule": ["formule"],
    "Type d'établissement": ["type_etablissement"],
    "Région": ["region"],
    "Canal d'acquisition": ["type_canal"],
}


def preparer(df: pd.DataFrame, note_par_defaut: float) -> pd.DataFrame:
    """Ajoute les variables dérivées. note_par_defaut : note moyenne de l'apprentissage, pour les mois sans note."""
    d = df.copy()
    d["log_tendance_usage"] = np.log(d["tendance_usage"])
    d["sans_commande_table"] = d["taux_commande_3m"].isna().astype(int)
    d["taux_commande_3m"] = d["taux_commande_3m"].fillna(0.0)
    d["tickets_2_ou_plus"] = (d["tickets_3m"] >= 2).astype(int)
    d["sans_note"] = d["satisfaction_6m"].isna().astype(int)
    d["satisfaction_6m"] = d["satisfaction_6m"].fillna(note_par_defaut)
    d["a_facture_retard_6m"] = (d["factures_retard_6m"] > 0).astype(int)
    annuel = d["periodicite_facturation"].eq("annuelle")
    d["echeance_annuelle"] = (annuel & (d["anciennete_mois"] % 12 == 11)).astype(int)
    d["facturation_mensuelle"] = (~annuel).astype(int)
    return d


def _matrice(pre, X):
    Z = pre.transform(X)
    return Z.toarray() if hasattr(Z, "toarray") else np.asarray(Z)


def contributions_logistique(pipeline, X: pd.DataFrame, X_reference: pd.DataFrame) -> pd.DataFrame:
    """Contribution de chaque facteur au logit, par ligne, par rapport à l'établissement moyen de X_reference.

    Régression logistique : logit = constante + somme(coefficient x variable transformée). En centrant chaque
    variable transformée sur sa moyenne d'apprentissage, la contribution d'un facteur dit de combien il éloigne
    l'établissement du risque moyen. Une contribution positive augmente le risque.
    """
    pre, lr = pipeline[0], pipeline[-1]
    centre = _matrice(pre, X_reference).mean(axis=0)
    contrib = (_matrice(pre, X) - centre) * lr.coef_[0]
    noms = pre.get_feature_names_out()
    par_colonne = pd.DataFrame(contrib, columns=noms, index=X.index)
    sortie = {}
    for facteur, variables in FACTEURS.items():
        cols = [n for n in noms if any(n == f"n__{v}" or n.startswith(f"c__{v}_") for v in variables)]
        sortie[facteur] = par_colonne[cols].sum(axis=1)
    return pd.DataFrame(sortie)


def trois_facteurs(contrib: pd.DataFrame) -> pd.DataFrame:
    """Les 3 facteurs qui augmentent le plus le risque (contribution positive), par ligne."""
    lignes = []
    for idx, ligne in contrib.iterrows():
        top = ligne[ligne > 0].sort_values(ascending=False).head(3)
        noms = list(top.index) + [None] * (3 - len(top))
        lignes.append({"facteur_1": noms[0], "facteur_2": noms[1], "facteur_3": noms[2]})
    return pd.DataFrame(lignes, index=contrib.index)


def auc_bootstrap(y, score, groupes, n: int = 1000, graine: int = 42):
    """AUC et intervalle à 95 % par bootstrap par établissement (les mois d'un même établissement restent ensemble)."""
    y, score, groupes = np.asarray(y), np.asarray(score), np.asarray(groupes)
    uniques = np.unique(groupes)
    index = {g: np.flatnonzero(groupes == g) for g in uniques}
    rng = np.random.default_rng(graine)
    valeurs = []
    for _ in range(n):
        tirage = np.concatenate([index[g] for g in rng.choice(uniques, size=len(uniques), replace=True)])
        if y[tirage].min() == y[tirage].max():
            continue
        valeurs.append(roc_auc_score(y[tirage], score[tirage]))
    return roc_auc_score(y, score), float(np.percentile(valeurs, 2.5)), float(np.percentile(valeurs, 97.5))


def enregistrer_fiche(nom: str, fiche: dict) -> None:
    """Écrit la fiche d'identité du modèle (JSON) dans 06_exports/modeles/fiches."""
    dossier = config.DOSSIER_MODELES / "fiches"
    dossier.mkdir(parents=True, exist_ok=True)
    fiche = {"modele": nom, "date": date.today().isoformat(), "autrice": "Sarra Abdeljaouad", **fiche}
    (dossier / f"{nom}.json").write_text(json.dumps(fiche, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
