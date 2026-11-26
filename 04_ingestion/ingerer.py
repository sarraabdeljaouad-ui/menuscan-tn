# -*- coding: utf-8 -*-
"""MenuScan TN - phase 3 : ingestion de la couche brute dans le schéma raw de menuscan_dwh.

Règle : rien n'est corrigé. Chaque fichier est chargé tel qu'il est arrivé, avec quatre colonnes techniques
(_lot_id, _fichier, _ligne, _charge_le). Les CSV sont stockés en texte, les JSON entiers dans une colonne JSONB.

Le journal raw.chargements garde l'empreinte SHA-256 de chaque fichier : un fichier déjà chargé et inchangé est sauté,
un fichier modifié est rechargé (ses anciennes lignes sont remplacées, sans doublon). Chaque fichier est chargé dans
sa propre transaction : un échec n'arrête pas les autres fichiers.

Usage, depuis la racine du dépôt, environnement Python activé, Docker lancé :
    python 04_ingestion/ingerer.py                      # charge ce qui est nouveau ou modifié
    python 04_ingestion/ingerer.py --reinitialiser      # supprime le schéma raw et recharge tout
    python 04_ingestion/ingerer.py --seulement tracking # ne traite que les fichiers dont le chemin contient « tracking »
"""
import argparse
import hashlib
import os
import io
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2 import sql

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chargeurs import PAR_FORMAT  # noqa: E402

RACINE = Path(__file__).resolve().parents[1]

# Fichier source -> table cible et format. La table porte le nom du système source et de l'entité.
SOURCES = [
    ("backoffice/abonnements.csv", "backoffice_abonnements", "csv"),
    ("backoffice/etablissements.csv", "backoffice_etablissements", "csv"),
    ("backoffice/formules.csv", "backoffice_formules", "csv"),
    ("backoffice/tables_salle.csv", "backoffice_tables_salle", "csv"),
    ("crm/prospects.csv", "crm_prospects", "csv"),
    ("facturation/factures.csv", "facturation_factures", "csv_fr"),
    ("marketing/campagnes_marketing.csv", "marketing_campagnes", "csv"),
    ("marketing/depenses_quotidiennes.csv", "marketing_depenses_quotidiennes", "csv_fr"),
    ("menus/articles.csv", "menus_articles", "csv"),
    ("menus/articles_prix_historique.csv", "menus_articles_prix_historique", "csv"),
    ("menus/categories_menu.csv", "menus_categories", "csv"),
    ("paiements_api/paiements.jsonl", "paiements_api_paiements", "json_api"),
    ("referentiels/canaux_acquisition.csv", "referentiels_canaux_acquisition", "csv"),
    ("referentiels/dim_calendrier.csv", "referentiels_calendrier", "csv"),
    ("referentiels/ref_villes.csv", "referentiels_villes", "csv"),
    ("support/tickets_support.csv", "support_tickets", "csv"),
    ("tracking/events_*.jsonl.gz", "tracking_events", "json_gz"),
    ("ventes/commandes/commandes_*.csv", "ventes_commandes", "csv"),
    ("ventes/lignes_commande/lignes_commande_*.csv", "ventes_lignes_commande", "csv"),
]
TECHNIQUES = [("_lot_id", "BIGINT NOT NULL"), ("_fichier", "TEXT NOT NULL"), ("_ligne", "INTEGER NOT NULL"),
              ("_charge_le", "TIMESTAMPTZ NOT NULL")]


def lire_env():
    """Variables de connexion : fichier .env, puis variables d'environnement POSTGRES_* qui l'emportent
    (dans les conteneurs Airflow, le serveur s'appelle postgres et écoute sur le port 5432)."""
    env = {}
    f = RACINE / ".env"
    if f.exists():
        for ligne in f.read_text(encoding="utf-8").splitlines():
            if "=" in ligne and not ligne.strip().startswith("#"):
                k, v = ligne.split("=", 1)
                env[k.strip()] = v.strip()
    env.update({k: v for k, v in os.environ.items() if k.startswith("POSTGRES_")})
    return env


def connexion():
    env = lire_env()
    return psycopg2.connect(host=env.get("POSTGRES_HOST", "127.0.0.1"), port=env.get("POSTGRES_PORT", "5440"),
                            user=env.get("POSTGRES_USER"), password=env.get("POSTGRES_PASSWORD"), dbname="menuscan_dwh",
                            connect_timeout=10)


def empreinte(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def preparer_table(cur, table, colonnes):
    """Crée la table si besoin ; ajoute les colonnes apparues dans un nouveau fichier (dérive de schéma), en texte."""
    cols = [(c, "TEXT") for c in colonnes] if colonnes is not None else [("donnees", "JSONB NOT NULL")]
    defs = sql.SQL(", ").join(sql.SQL("{} {}").format(sql.Identifier(c), sql.SQL(t)) for c, t in TECHNIQUES + cols)
    cur.execute(sql.SQL("CREATE TABLE IF NOT EXISTS raw.{} ({})").format(sql.Identifier(table), defs))
    for c, t in cols:
        cur.execute(sql.SQL("ALTER TABLE raw.{} ADD COLUMN IF NOT EXISTS {} {}").format(sql.Identifier(table), sql.Identifier(c), sql.SQL(t)))
    cur.execute(sql.SQL("CREATE INDEX IF NOT EXISTS {} ON raw.{} (_fichier)").format(sql.Identifier(f"ix_{table}_fichier"), sql.Identifier(table)))


def charger_fichier(conn, lot, source, rel, table, fmt):
    chemin = source / rel
    sha, octets, debut = empreinte(chemin), chemin.stat().st_size, datetime.now(timezone.utc)
    t0 = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute("""SELECT empreinte_sha256 FROM raw.chargements WHERE fichier = %s AND statut IN ('charge', 'recharge')
                       ORDER BY chargement_id DESC LIMIT 1""", (rel,))
        dernier = cur.fetchone()
    journal = dict(lot_id=lot, fichier=rel, table_cible=f"raw.{table}", format=fmt, empreinte_sha256=sha, octets=octets, debut=debut)
    if dernier and dernier[0] == sha:
        ecrire_journal(conn, journal, statut="deja_charge", t0=t0, message="Fichier inchangé depuis le dernier chargement")
        conn.commit()
        return "deja_charge", 0
    statut = "recharge" if dernier else "charge"
    try:
        with conn.cursor() as cur:
            colonnes, enregistrements = PAR_FORMAT[fmt].lire(chemin)
            preparer_table(cur, table, colonnes)
            if dernier:  # fichier modifié : ses anciennes lignes et ses anciens rejets sont remplacés
                cur.execute(sql.SQL("DELETE FROM raw.{} WHERE _fichier = %s").format(sql.Identifier(table)), (rel,))
                cur.execute("DELETE FROM raw.rejets WHERE fichier = %s", (rel,))
            tampon, lues, rejets = io.StringIO(), 0, []
            ecrivain = csv.writer(tampon, lineterminator="\n")
            for e in enregistrements:
                lues += 1
                if e[1] is None:
                    rejets.append((lot, rel, e[0], e[2], e[3]))
                    continue
                ecrivain.writerow([lot, rel, e[0], debut.isoformat()] + [v if v != "" else None for v in e[1]])
            cols = [c for c, _ in TECHNIQUES] + (colonnes if colonnes is not None else ["donnees"])
            tampon.seek(0)
            cur.copy_expert(sql.SQL("COPY raw.{} ({}) FROM STDIN WITH (FORMAT csv)").format(
                sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, cols))).as_string(cur), tampon)
            ecrites = cur.rowcount
            if rejets:
                cur.executemany("INSERT INTO raw.rejets (lot_id, fichier, ligne, motif, contenu) VALUES (%s, %s, %s, %s, %s)", rejets)
        ecrire_journal(conn, journal, statut=statut, t0=t0, lignes_lues=lues, lignes_ecrites=ecrites, lignes_rejetees=len(rejets))
        conn.commit()
        return statut, ecrites
    except Exception as err:  # le fichier est annulé, l'échec est journalisé, les autres fichiers continuent
        conn.rollback()
        ecrire_journal(conn, journal, statut="echec", t0=t0, message=f"{type(err).__name__} : {err}"[:1000])
        conn.commit()
        return "echec", 0


def ecrire_journal(conn, j, statut, t0, lignes_lues=None, lignes_ecrites=None, lignes_rejetees=None, message=None):
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO raw.chargements (lot_id, fichier, table_cible, format, empreinte_sha256, octets, lignes_lues,
                       lignes_ecrites, lignes_rejetees, debut, fin, duree_s, statut, message)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), %s, %s, %s)""",
                    (j["lot_id"], j["fichier"], j["table_cible"], j["format"], j["empreinte_sha256"], j["octets"], lignes_lues,
                     lignes_ecrites, lignes_rejetees, j["debut"], round(time.perf_counter() - t0, 3), statut, message))


def main():
    ap = argparse.ArgumentParser(description="Ingestion de la couche brute MenuScan TN dans raw (menuscan_dwh)")
    ap.add_argument("--source", default="menuscan_dataset/donnees_brutes", help="dossier donnees_brutes du jeu complet")
    ap.add_argument("--reinitialiser", action="store_true", help="supprimer le schéma raw (données et journal) avant de charger")
    ap.add_argument("--seulement", default="", help="ne traiter que les fichiers dont le chemin contient ce texte")
    a = ap.parse_args()
    source = Path(a.source) if Path(a.source).is_absolute() else RACINE / a.source
    if not source.is_dir():
        sys.exit(f"Dossier introuvable : {source}. Décompresser la Release v1.1-donnees à la racine du dépôt.")
    fichiers = []
    for motif, table, fmt in SOURCES:
        trouves = sorted(source.glob(motif))
        if not trouves:
            sys.exit(f"Aucun fichier pour {motif} dans {source}")
        fichiers += [(str(p.relative_to(source)).replace("\\", "/"), table, fmt) for p in trouves]
    fichiers = [f for f in fichiers if a.seulement in f[0]]

    conn = connexion()
    with conn.cursor() as cur:
        if a.reinitialiser:
            cur.execute("DROP SCHEMA IF EXISTS raw CASCADE")
        cur.execute((Path(__file__).resolve().parent / "journal.sql").read_text(encoding="utf-8"))
        cur.execute("SELECT nextval('raw.seq_lot')")
        lot = cur.fetchone()[0]
    conn.commit()

    print(f"Lot {lot} : {len(fichiers)} fichiers à traiter depuis {source}")
    t0, bilan, lignes = time.perf_counter(), {"charge": 0, "recharge": 0, "deja_charge": 0, "echec": 0}, 0
    for i, (rel, table, fmt) in enumerate(fichiers, 1):
        statut, n = charger_fichier(conn, lot, source, rel, table, fmt)
        bilan[statut] += 1
        lignes += n
        if statut != "deja_charge" or i == len(fichiers):
            print(f"  [{i:3d}/{len(fichiers)}] {statut:11s} {rel:55s} {f'{n:,}'.replace(',', ' '):>9} lignes")
    conn.close()
    milliers = f"{lignes:,}".replace(",", " ")
    print(f"\nTerminé en {time.perf_counter() - t0:.0f} s : {bilan['charge']} chargés, {bilan['recharge']} rechargés, "
          f"{bilan['deja_charge']} inchangés, {bilan['echec']} en échec ; {milliers} lignes écrites.")
    if bilan["echec"]:
        print("Voir le détail : SELECT fichier, message FROM raw.chargements WHERE statut = 'echec' AND lot_id = %d;" % lot)
        sys.exit(1)


if __name__ == "__main__":
    main()
