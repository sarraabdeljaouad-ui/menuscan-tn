# -*- coding: utf-8 -*-
"""MenuScan TN - jeu de démonstration (tâche T2.2).

Extrait de la couche de référence du jeu complet (Release v1.1-donnees) : 20 établissements, activité du 01/01/2026
au 30/06/2026, au format Parquet. Le sous-ensemble respecte toutes les clés étrangères du schéma.

Règles de découpage :
- 20 établissements tirés au sort (graine fixe) parmi ceux abonnés pendant la période, par formule (7 Essentiel,
  8 Commande, 5 Pro), avec ETB0005 (Café Les Arcades, l'établissement de démonstration de l'application), au moins un
  établissement signé et un établissement résilié pendant la période ;
- activité (sessions, événements, commandes, lignes) et dépenses marketing : période seulement ;
- abonnements, factures, paiements, tickets, menus, prix et tables de ces établissements : historique complet
  (les colonnes d'état des établissements sont une photo au 31/12/2026, comme dans le jeu complet) ;
- référentiels, calendrier et campagnes : complets ;
- prospects : ceux convertis en l'un des 20 établissements, et les prospects non convertis contactés pendant la
  période ; un parrain hors du jeu de démonstration est mis à vide (compté dans le manifeste).

Usage, depuis la racine du dépôt, environnement Python activé :
    python 03_generateur/creer_demo.py --source menuscan_dataset/donnees_reference
"""
import argparse
import glob
import hashlib
import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

GRAINE = 2027
DEBUT, FIN = pd.Timestamp("2026-01-01"), pd.Timestamp("2026-06-30 23:59:59")
QUOTAS = {"FRM01": 7, "FRM02": 8, "FRM03": 5}
OBLIGATOIRE = "ETB0005"
SORTIE = Path(__file__).resolve().parent / "demo_data"
SCHEMA = Path(__file__).resolve().parents[1] / "02_oltp" / "schema_postgres.sql"


def types_colonnes():
    """Type PostgreSQL de chaque colonne, lu dans le schéma du dépôt : les fichiers Parquet gardent ces types
    (un entier reste un entier même avec des cases vides, une date reste une date)."""
    ddl, r = SCHEMA.read_text(encoding="utf-8"), {}
    for table, corps in re.findall(r"CREATE TABLE (\w+) \((.*?)\n\);", ddl, flags=re.S):
        r[table] = {c: t for c, t in re.findall(r"^\s+(\w+) (INTEGER|SMALLINT|BIGINT|BOOLEAN|DATE|TIMESTAMP)\b", corps, flags=re.M)}
    return r


def lire(source, table, types):
    if table == "evenements":  # 36 fichiers mensuels
        df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(source, "evenements", "*.csv")))], ignore_index=True)
    else:
        df = pd.read_csv(os.path.join(source, f"{table}.csv"))
    for c, t in types.get(table, {}).items():
        if c not in df:
            continue
        if t == "DATE":
            df[c] = pd.to_datetime(df[c]).dt.date
        elif t == "TIMESTAMP":
            df[c] = pd.to_datetime(df[c])
        elif t == "BOOLEAN":
            df[c] = df[c].map({True: True, False: False, "True": True, "False": False, "true": True, "false": False}).astype("boolean")
        else:
            df[c] = pd.to_numeric(df[c]).astype({"SMALLINT": "Int16", "INTEGER": "Int32", "BIGINT": "Int64"}[t])
    return df


def choisir(t):
    """Tirage des 20 établissements."""
    ab, et, se = t["abonnements"], t["etablissements"], t["sessions"]
    d0, d1 = DEBUT.date(), FIN.date()
    actifs = ab[(ab.date_debut <= d1) & (ab.date_fin.isna() | (ab.date_fin.apply(lambda x: x if pd.notna(x) else d1) >= d0))]
    milieu = pd.Timestamp("2026-04-01").date()
    # formule de référence : celle de l'abonnement en cours au 01/04/2026, sinon le dernier de la période
    actifs = actifs.assign(couvre=(actifs.date_debut <= milieu) & (actifs.date_fin.isna() | (actifs.date_fin.apply(lambda x: x if pd.notna(x) else d1) >= milieu)))
    ref = actifs.sort_values(["etablissement_id", "couvre", "date_debut"]).groupby("etablissement_id").tail(1).set_index("etablissement_id").formule_id
    avec_activite = set(se[(se.debut_session >= DEBUT) & (se.debut_session <= FIN)].etablissement_id)
    cand = et[et.etablissement_id.isin(ref.index) & et.etablissement_id.isin(avec_activite)].copy()
    cand["formule"] = cand.etablissement_id.map(ref)
    cand["signe"] = pd.to_datetime(cand.date_signature).between(DEBUT, FIN)
    cand["resilie"] = pd.to_datetime(cand.date_resiliation).between(DEBUT, FIN)
    rng = np.random.default_rng(GRAINE)
    choix = [OBLIGATOIRE]
    for col in ("signe", "resilie"):  # au moins un établissement signé et un résilié pendant la période
        pool = cand[cand[col] & ~cand.etablissement_id.isin(choix)]
        if len(pool):
            choix.append(pool.etablissement_id.iloc[rng.integers(len(pool))])
    for f, n in QUOTAS.items():
        deja = int(cand[cand.etablissement_id.isin(choix)].formule.eq(f).sum())
        pool = cand[(cand.formule == f) & ~cand.etablissement_id.isin(choix)].etablissement_id.tolist()
        choix += list(rng.choice(pool, size=max(0, n - deja), replace=False))
    return sorted(choix), cand.set_index("etablissement_id")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="menuscan_dataset/donnees_reference", help="dossier donnees_reference du jeu complet")
    a = ap.parse_args()
    types = types_colonnes()
    noms = [Path(f).stem for f in glob.glob(os.path.join(a.source, "*.csv"))] + ["evenements"]
    t = {n: lire(a.source, n, types) for n in noms}
    sel, cand = choisir(t)
    E = set(sel)
    dans = lambda df: df[df.etablissement_id.isin(E)]
    periode = lambda s: (s >= DEBUT) & (s <= FIN)
    d = {}
    for n in ("dim_calendrier", "ref_villes", "formules", "canaux_acquisition", "campagnes_marketing"):
        d[n] = t[n]
    md = t["marketing_depenses_quotidiennes"]
    d["marketing_depenses_quotidiennes"] = md[periode(pd.to_datetime(md["date"]))]
    for n in ("etablissements", "abonnements", "factures", "tickets_support", "categories_menu", "articles", "tables_salle"):
        d[n] = dans(t[n])
    d["articles_prix_historique"] = t["articles_prix_historique"][t["articles_prix_historique"].article_id.isin(d["articles"].article_id)]
    d["paiements"] = t["paiements"][t["paiements"].facture_id.isin(d["factures"].facture_id)]
    se = dans(t["sessions"]); d["sessions"] = se[periode(se.debut_session)]
    d["evenements"] = t["evenements"][t["evenements"].session_id.isin(d["sessions"].session_id)]
    co = t["commandes"]; d["commandes"] = co[co.session_id.isin(d["sessions"].session_id)]
    d["lignes_commande"] = t["lignes_commande"][t["lignes_commande"].commande_id.isin(d["commandes"].commande_id)]
    pr = t["prospects"]
    garde = pr.etablissement_id.isin(E) | (pr.etablissement_id.isna() & periode(pd.to_datetime(pr.date_contact)))
    pr = pr[garde].copy()
    parrains_vides = int((pr.parrain_etablissement_id.notna() & ~pr.parrain_etablissement_id.isin(E)).sum())
    pr.loc[~pr.parrain_etablissement_id.isin(E), "parrain_etablissement_id"] = None
    d["prospects"] = pr
    # les campagnes citées doivent exister (elles sont gardées entières) ; contrôle des clés étrangères principales
    assert d["etablissements"].prospect_id.dropna().isin(d["prospects"].prospect_id).all(), "prospect d'un établissement absent"
    assert d["lignes_commande"].article_id.isin(d["articles"].article_id).all()
    assert d["evenements"].article_id.dropna().isin(d["articles"].article_id).all()
    assert d["commandes"].table_id.isin(d["tables_salle"].table_id).all()

    SORTIE.mkdir(parents=True, exist_ok=True)
    for f in SORTIE.glob("*.parquet"):
        f.unlink()
    manifeste = {"source": "Release v1.1-donnees, couche donnees_reference", "graine": GRAINE,
                 "periode_activite": [str(DEBUT.date()), str(FIN.date())], "etablissements": sel,
                 "formules": {e: cand.formule.get(e) for e in sel}, "parrains_mis_a_vide": parrains_vides, "tables": {}}
    for n in sorted(d):
        chemin = SORTIE / f"{n}.parquet"
        d[n].reset_index(drop=True).to_parquet(chemin, index=False, compression="zstd")
        manifeste["tables"][n] = {"lignes": int(len(d[n])), "sha256": hashlib.sha256(chemin.read_bytes()).hexdigest()}
    (SORTIE / "manifeste.json").write_text(json.dumps(manifeste, ensure_ascii=False, indent=2), encoding="utf-8")
    tot = sum(v["lignes"] for v in manifeste["tables"].values())
    print(f"{len(d)} tables, {tot} lignes, {len(sel)} établissements : {', '.join(sel)}")
    print(f"parrains hors démo mis à vide : {parrains_vides}")


if __name__ == "__main__":
    main()
