# -*- coding: utf-8 -*-
"""Charge la base applicative menuscan_app (schéma menuscan) à partir de la couche de référence.

Usage, depuis la racine du dépôt, environnement Python activé :
    python 02_oltp/charger_base_app.py                 # crée le schéma s'il est absent, puis charge
    python 02_oltp/charger_base_app.py --reinitialiser # supprime le schéma menuscan et recharge tout
    python 02_oltp/charger_base_app.py --migrer        # applique seulement les migrations (base déjà chargée)
    python 02_oltp/charger_base_app.py --controles     # relance seulement les contrôles qualité

Étapes :
  1. crée les tables (02_oltp/schema_postgres.sql) ;
  2. charge les 20 tables dans l'ordre des clés étrangères, avec COPY, puis ajoute les clés circulaires
     entre prospects et etablissements ;
  3. compare le nombre de lignes chargées au nombre de lignes des fichiers ;
  4. applique les migrations de 02_oltp/migrations/ (évolutions du modèle pour l'application) ;
  5. exécute les contrôles de 02_oltp/controles_qualite.sql (0 violation attendue partout) ;
  6. écrit un rapport dans 02_oltp/rapport_chargement.md (chargement complet seulement).

Sortie 0 si tout est conforme, 1 sinon.
"""
import argparse
import csv
import glob
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import psycopg2

RACINE = Path(__file__).resolve().parent.parent
ICI = Path(__file__).resolve().parent
ORDRE = ["dim_calendrier", "ref_villes", "formules", "canaux_acquisition", "campagnes_marketing",
         "marketing_depenses_quotidiennes", "prospects", "etablissements", "abonnements", "factures",
         "paiements", "tickets_support", "categories_menu", "articles", "articles_prix_historique",
         "tables_salle", "sessions", "evenements", "commandes", "lignes_commande"]


def lire_env():
    env = {}
    f = RACINE / ".env"
    if f.exists():
        for ligne in f.read_text(encoding="utf-8").splitlines():
            if "=" in ligne and not ligne.strip().startswith("#"):
                k, v = ligne.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def fichiers(dossier, table):
    if table == "evenements":
        return sorted(glob.glob(str(dossier / "evenements" / "evenements_*.csv")))
    return [str(dossier / f"{table}.csv")]


def compter_lignes(chemins):
    n = 0
    for c in chemins:
        with open(c, encoding="utf-8", newline="") as f:
            n += sum(1 for _ in csv.reader(f)) - 1
    return n


MARQUEUR_CLES = "-- Clés circulaires ajoutées après création"


def executer_sql(cur, texte):
    """Exécute un texte SQL instruction par instruction (les commentaires ne contiennent pas de point-virgule)."""
    for instr in texte.split(";"):
        lignes = [l for l in instr.splitlines() if l.strip() and not l.strip().startswith("--")]
        if lignes:
            cur.execute(instr)


def appliquer_migrations(cur):
    for f in sorted((ICI / "migrations").glob("*.sql")):
        executer_sql(cur, f.read_text(encoding="utf-8"))
        print(f"   {f.name} appliquée")


def controler(cur):
    cur.execute("SET search_path TO menuscan")
    sql = (ICI / "controles_qualite.sql").read_text(encoding="utf-8")
    cur.execute(sql.split("SET search_path TO menuscan;", 1)[1].strip().rstrip(";"))
    ctl = cur.fetchall()
    viol = [r for r in ctl if r[2] != 0]
    print(f"   {len(ctl)} contrôles, {len(viol)} en violation")
    for r in viol:
        print(f"   {r[0]} {r[1]} : {r[2]} violation(s)")
    return ctl, viol


def connecter():
    env = lire_env()
    return psycopg2.connect(host=env.get("POSTGRES_HOST", "127.0.0.1"), port=env.get("POSTGRES_PORT", "5440"),
                            user=env.get("POSTGRES_USER"), password=env.get("POSTGRES_PASSWORD"), dbname="menuscan_app", connect_timeout=10)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--donnees", default=str(RACINE / "menuscan_dataset" / "donnees_reference"),
                   help="dossier donnees_reference du jeu MenuScan TN")
    p.add_argument("--reinitialiser", action="store_true", help="supprime puis recrée le schéma menuscan")
    p.add_argument("--migrer", action="store_true", help="applique seulement les migrations")
    p.add_argument("--controles", action="store_true", help="relance seulement les contrôles qualité")
    a = p.parse_args()
    if a.migrer or a.controles:
        cnx = connecter()
        cur = cnx.cursor()
        if a.migrer:
            print("Migrations")
            appliquer_migrations(cur)
            cnx.commit()
        print("Contrôles qualité")
        _, viol = controler(cur)
        cnx.close()
        print(f"\nRésultat : {'CONFORME' if not viol else 'NON CONFORME'}")
        sys.exit(0 if not viol else 1)
    dossier = Path(a.donnees)
    if not (dossier / "etablissements.csv").exists():
        sys.exit(f"Dossier introuvable ou incomplet : {dossier}\n"
                 "Décompresser menuscan_dataset_v1.0.zip (Release du dépôt) à la racine du dépôt, ou passer --donnees.")

    cnx = connecter()
    cur = cnx.cursor()
    debut = time.time()

    cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'menuscan')")
    existe = cur.fetchone()[0]
    if existe and not a.reinitialiser:
        cur.execute("SELECT COUNT(*) FROM menuscan.etablissements")
        if cur.fetchone()[0] > 0:
            sys.exit("Le schéma menuscan est déjà chargé. Relancer avec --reinitialiser pour tout recharger.")
    if existe:
        cur.execute("DROP SCHEMA menuscan CASCADE")
    print("1. Création des tables")
    ddl = (ICI / "schema_postgres.sql").read_text(encoding="utf-8")
    tables_sql, cles_sql = ddl.split(MARQUEUR_CLES, 1)  # clés circulaires prospects <-> etablissements : ajoutées après chargement
    executer_sql(cur, tables_sql)
    cur.execute("SET search_path TO menuscan")

    print("2. Chargement")
    res = []
    for t in ORDRE:
        chemins = fichiers(dossier, t)
        t0 = time.time()
        for c in chemins:
            with open(c, encoding="utf-8", newline="") as f:
                entete = f.readline().strip()
                f.seek(0)
                cur.copy_expert(f"COPY {t} ({entete}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')", f)
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        en_base = cur.fetchone()[0]
        attendu = compter_lignes(chemins)
        res.append((t, len(chemins), attendu, en_base, time.time() - t0))
        print(f"   {t:<34} {en_base:>10,} lignes  {'OK' if en_base == attendu else 'ÉCART'}".replace(",", " "))
    executer_sql(cur, cles_sql)
    cnx.commit()

    print("3. Migrations")
    appliquer_migrations(cur)
    cnx.commit()

    print("4. Contrôles qualité")
    ctl, viol = controler(cur)
    cnx.close()

    ecarts = [r for r in res if r[2] != r[3]]
    ok = not ecarts and not viol
    duree = time.time() - debut
    lignes = ["# Rapport de chargement de la base applicative", "",
              f"**Date :** {datetime.now():%d/%m/%Y %H:%M} · **Base :** menuscan_app, schéma menuscan · **Source :** `{dossier.name}` · **Durée :** {duree:.0f} s", "",
              "## Tables chargées", "", "| Table | Fichiers | Lignes dans les fichiers | Lignes en base | Statut |", "|---|---:|---:|---:|---|"]
    for t, nf, att, eb, _ in res:
        lignes.append(f"| {t} | {nf} | {att:,} | {eb:,} | {'Conforme' if att == eb else 'Écart'} |".replace(",", " "))
    lignes.append(f"| **Total** | {sum(r[1] for r in res)} | {sum(r[2] for r in res):,} | {sum(r[3] for r in res):,} | |".replace(",", " "))
    lignes += ["", "## Contrôles qualité", "", "| Règle | Objet | Violations |", "|---|---|---:|"]
    lignes += [f"| {r[0]} | {r[1]} | {r[2]} |" for r in ctl]
    lignes += ["", f"**Résultat : {'conforme' if ok else 'non conforme'}** ({len(res) - len(ecarts)} tables sur {len(res)} conformes, {len(ctl) - len(viol)} contrôles sur {len(ctl)} à 0)."]
    (ICI / "rapport_chargement.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"\nRésultat : {'CONFORME' if ok else 'NON CONFORME'} en {duree:.0f} s. Rapport : 02_oltp/rapport_chargement.md")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
