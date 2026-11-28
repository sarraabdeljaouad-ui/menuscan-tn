# -*- coding: utf-8 -*-
"""Copie les résultats de la phase 7 (schéma ml de l'entrepôt) dans la base applicative (T8.1, exigence EF-14).

L'application ne lit jamais l'entrepôt : elle lit des copies dans menuscan_app (migration 010).
La copie se fait en une seule transaction côté application : en cas d'erreur, les anciennes copies restent en place.

Usage, depuis la racine du dépôt, environnement Python activé, après 08_analyse_ml/03_machine_learning/04_publication_resultats :
    python 02_oltp/copier_resultats_ml.py

Contrôles en fin de copie : nombre de lignes identique à la source, aucun établissement inconnu.
"""
import os
import sys
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values

from charger_base_app import connecter, lire_env

TABLES = {
    # table de l'application : (requête sur l'entrepôt, colonnes)
    "ml_score_resiliation": (
        """SELECT s.etablissement_id, s.mois_observe, s.probabilite, s.rang, s.alerte, s.facteur_1, s.facteur_2,
                  s.facteur_3, a.mrr_ht, s.version_modele, s.publie_le
           FROM ml.score_resiliation s
           LEFT JOIN marts.fait_abonnement_mensuel a ON a.etablissement_id = s.etablissement_id AND a.mois = s.mois_observe""",
        "etablissement_id, mois_observe, probabilite, rang, alerte, facteur_1, facteur_2, facteur_3, mrr_ht, "
        "version_modele, publie_le"),
    "ml_candidat_commande": (
        """SELECT etablissement_id, sessions_table_jour_3m, seuil_usage, probabilite_resiliation, publie_le
           FROM ml.candidat_commande""",
        "etablissement_id, sessions_table_jour_3m, seuil_usage, probabilite_resiliation, publie_le"),
    "ml_recommandation_plat": (
        "SELECT etablissement_id, plat, rang, plat_recommande, motif, publie_le FROM ml.recommandation_plat",
        "etablissement_id, plat, rang, plat_recommande, motif, publie_le"),
}


def connecter_entrepot():
    env = lire_env()
    return psycopg2.connect(host=env.get("POSTGRES_HOST", "127.0.0.1"), port=env.get("POSTGRES_PORT", "5440"),
                            user=env.get("POSTGRES_USER"), password=env.get("POSTGRES_PASSWORD"),
                            dbname=os.environ.get("MENUSCAN_DWH", "menuscan_dwh"), connect_timeout=10)


def main():
    dwh, app = connecter_entrepot(), connecter()
    try:
        with dwh.cursor() as cur:
            cur.execute("SELECT max(publie_le) FROM ml.journal_publication")
            publie_le = cur.fetchone()[0]
            if publie_le is None:
                sys.exit("Schéma ml vide : lancer d'abord 08_analyse_ml/03_machine_learning/04_publication_resultats.")
            donnees = {}
            for table, (sql, _) in TABLES.items():
                cur.execute(sql)
                donnees[table] = cur.fetchall()
        with app.cursor() as cur:
            cur.execute("SET search_path TO menuscan")
            cur.execute("SELECT 1 FROM migrations WHERE migration_id = '010_resultats_ml'")
            if cur.fetchone() is None:
                sys.exit("Migration 010 manquante : lancer python 02_oltp/charger_base_app.py --migrer")
            copie_le = datetime.now().replace(microsecond=0)
            for table, (_, colonnes) in TABLES.items():
                cur.execute(f"DELETE FROM {table}")
                execute_values(cur, f"INSERT INTO {table} ({colonnes}) VALUES %s", donnees[table])
                cur.execute(f"SELECT count(*) FROM {table}")
                n = cur.fetchone()[0]
                if n != len(donnees[table]):
                    raise RuntimeError(f"{table} : {n} lignes copiées pour {len(donnees[table])} lues")
                cur.execute("INSERT INTO ml_copie (copie_le, publie_le, nom_table, lignes) VALUES (%s, %s, %s, %s)",
                            (copie_le, publie_le, table, n))
                print(f"   {table} : {n} lignes")
        app.commit()
        print(f"Copie terminée : résultats publiés le {publie_le:%d/%m/%Y %H:%M}, copiés le {copie_le:%d/%m/%Y %H:%M}")
    except Exception:
        app.rollback()
        raise
    finally:
        dwh.close()
        app.close()


if __name__ == "__main__":
    main()
