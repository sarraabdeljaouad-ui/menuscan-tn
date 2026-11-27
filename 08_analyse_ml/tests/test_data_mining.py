import numpy as np
import pandas as pd

from menuscan_analytics import data_mining as dm


def test_lift_ajuste_neutralise_l_effet_etablissement():
    """A et B sont proposés dans les mêmes établissements mais choisis au hasard : lift ajusté proche de 1.
    Chaque commande contient aussi une boisson X, pour que toutes les commandes existent (une commande vide
    n'apparaît pas dans les lignes, ce qui fausserait l'indépendance)."""
    rng = np.random.default_rng(0)
    lignes = []
    for e in range(20):
        offre = ["A", "B"] if e < 10 else ["C", "D"]
        for c in range(200):
            lignes.append((f"E{e}", f"E{e}-{c}", "X"))
            for plat in offre:
                if rng.random() < 0.5:
                    lignes.append((f"E{e}", f"E{e}-{c}", plat))
    df = pd.DataFrame(lignes, columns=["etablissement_id", "commande_id", "nom_article"])
    r = dm.regles(df, "nom_article")
    ab = r[(r.antecedent == "A") & (r.consequent == "B")].iloc[0]
    assert abs(ab.lift_ajuste - 1) < 0.1 and not ab.retenue


def test_lift_ajuste_detecte_une_association():
    rng = np.random.default_rng(1)
    lignes = []
    for e in range(10):
        for c in range(400):
            lignes.append((f"E{e}", f"E{e}-{c}", "X"))
            a = rng.random() < 0.3
            b = rng.random() < (0.6 if a else 0.2)
            for plat, pris in (("A", a), ("B", b), ("C", rng.random() < 0.3)):
                if pris:
                    lignes.append((f"E{e}", f"E{e}-{c}", plat))
    df = pd.DataFrame(lignes, columns=["etablissement_id", "commande_id", "nom_article"])
    r = dm.regles(df, "nom_article")
    assert r.loc[(r.antecedent == "A") & (r.consequent == "B"), "retenue"].item()
    assert not r.loc[(r.antecedent == "A") & (r.consequent == "C"), "retenue"].item()


def test_elasticite_retrouve_la_valeur_simulee():
    """Données simulées avec une élasticité de -1 : l'estimation doit en être proche."""
    rng = np.random.default_rng(2)
    lignes = []
    for e in range(40):
        for k in range(4):
            pop, prix0 = rng.uniform(1, 3), rng.uniform(5, 15)
            hausse = k < 2                                  # 2 articles sur 4 augmentent au mois 6
            for m in range(12):
                prix = prix0 * (1.10 if hausse and m >= 6 else 1.0)
                q = rng.poisson(pop * 8 * (prix / prix0) ** -1.0)
                lignes.append({"etablissement_id": f"E{e}", "article_id": f"E{e}-A{k}", "mois": m,
                               "cellule": f"E{e}|{m}", "prix_ttc": prix, "q": q})
    est, nb = dm.elasticite(pd.DataFrame(lignes))
    assert nb == 80 and abs(est + 1.0) < 0.35
