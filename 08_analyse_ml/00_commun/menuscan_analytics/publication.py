"""publication.py : écriture des résultats dans le schéma ml de l'entrepôt, puis contrôles.

Toutes les tables sont remplacées dans UNE transaction : en cas d'erreur, rien n'est modifié et Power BI garde
la publication précédente. Chaque publication laisse une ligne par table dans ml.journal_publication.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
from sqlalchemy import text

from . import chargement, config

SCRIPT_DDL = config.RACINE / "00_commun" / "sql" / "01_schema_ml.sql"
ORDRE = ["score_resiliation", "candidat_commande", "regle_association", "recommandation_plat",
         "elasticite_categorie", "registre_modele"]


def creer_schema() -> None:
    """Crée le schéma ml et ses tables s'ils n'existent pas (script idempotent)."""
    with chargement.moteur().begin() as c:
        c.execute(text(SCRIPT_DDL.read_text(encoding="utf-8")))


def publier(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Vide puis remplit chaque table ml.<nom> avec le DataFrame donné, dans une seule transaction.

    Renvoie le journal de cette publication (une ligne par table).
    """
    inconnues = set(tables) - set(ORDRE)
    if inconnues:
        raise ValueError(f"tables inconnues : {sorted(inconnues)}")
    creer_schema()
    horodatage = datetime.now().replace(microsecond=0)
    journal = []
    with chargement.moteur().begin() as c:
        for nom in ORDRE:
            if nom not in tables:
                continue
            df = tables[nom].assign(publie_le=horodatage)
            c.execute(text(f"delete from ml.{nom}"))
            df.to_sql(nom, c, schema="ml", if_exists="append", index=False, method="multi", chunksize=500)
            journal.append({"publie_le": horodatage, "nom_table": nom, "lignes": len(df), "statut": "OK",
                            "message": None})
        pd.DataFrame(journal).to_sql("journal_publication", c, schema="ml", if_exists="append", index=False)
    return pd.DataFrame(journal)


CONTROLES = [
    ("P1", "Scores : un par établissement actif au 31/12/2026",
     "select (select count(*) from ml.score_resiliation) - (select count(*) from marts.dim_etablissement "
     "where date_mise_en_service <= '2026-12-31' and (date_resiliation is null or date_resiliation > '2026-12-31'))"),
    ("P2", "Scores : établissements inconnus de dim_etablissement",
     "select count(*) from ml.score_resiliation s left join marts.dim_etablissement e using (etablissement_id) "
     "where e.etablissement_id is null"),
    ("P3", "Scores : alertes = 10 % arrondi au supérieur",
     "select count(*) filter (where alerte) - ceil(0.10 * count(*)) from ml.score_resiliation"),
    ("P4", "Recommandations : établissements hors formule Pro en décembre 2026",
     "select count(distinct r.etablissement_id) from ml.recommandation_plat r "
     "join marts.fait_abonnement_mensuel a on a.etablissement_id = r.etablissement_id and a.mois = '2026-12-01' "
     "join marts.dim_formule f using (formule_id) where f.nom_formule <> 'Pro'"),
    ("P5", "Recommandations : plat recommandé absent de la carte actuelle",
     "select count(*) from ml.recommandation_plat r where not exists (select 1 from marts.dim_article a "
     "where a.etablissement_id = r.etablissement_id and a.nom_article = r.plat_recommande and a.est_prix_actuel)"),
    ("P6", "Candidats : établissements qui ne sont pas en formule Essentiel en décembre 2026",
     "select count(*) from ml.candidat_commande c join marts.fait_abonnement_mensuel a "
     "on a.etablissement_id = c.etablissement_id and a.mois = '2026-12-01' join marts.dim_formule f using (formule_id) "
     "where f.nom_formule <> 'Essentiel'"),
    ("P7", "Élasticités : intervalle qui ne contient pas l'estimation",
     "select count(*) from ml.elasticite_categorie where elasticite not between bas_95 and haut_95"),
    ("P8", "Journal : tables publiées lors de la dernière publication",
     "select 6 - count(*) from ml.journal_publication where publie_le = (select max(publie_le) from ml.journal_publication)"),
]


def controler() -> pd.DataFrame:
    """Contrôles après publication : chaque requête doit renvoyer 0."""
    lignes = []
    with chargement.moteur().connect() as c:
        for code, libelle, sql in CONTROLES:
            v = c.execute(text(sql)).scalar()
            lignes.append({"code": code, "controle": libelle, "valeur": v, "statut": "OK" if v == 0 else "ÉCART"})
    return pd.DataFrame(lignes)
