"""MenuScan TN - phase 5 : chaîne complète, de la couche brute à l'entrepôt validé.

Ordre des tâches (chacune attend la réussite de la précédente) :
    verifier_sources -> ingerer -> controler_volumes -> dbt_build -> controler_entrepot

Chaque tâche lance le même script que celui qu'on lance à la main depuis la racine du dépôt :
le DAG n'ajoute aucune logique de traitement, il enchaîne, journalise et s'arrête à la première erreur.
Planification : tous les jours à minuit, heure de Tunis (la chaîne TuniShop tourne à 22 h sous SQL Server Agent). Un DAG est en pause à sa création : l'activer dans l'interface.
Auteure : Sarra Abdeljaouad.
"""
import os
from datetime import timedelta

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

RACINE = os.environ.get("MENUSCAN_RACINE", "/opt/menuscan")      # dépôt monté dans les conteneurs
PYTHON = os.environ.get("MENUSCAN_PYTHON", "python")              # environnement de nos scripts (dbt, pandas)


def commande(script, *arguments):
    """Commande bash qui lance un script du dépôt depuis sa racine ; un code de retour non nul fait échouer la tâche."""
    return f'cd "{RACINE}" && "{PYTHON}" {script} {" ".join(arguments)}'.strip()


with DAG(
    dag_id="menuscan_chaine_complete",
    description="Ingestion, contrôle des volumes, dbt build, contrôle de l'entrepôt",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2026, 11, 1, tz="Africa/Tunis"),
    catchup=False,                     # pas de rattrapage des jours passés
    max_active_runs=1,                 # jamais deux chaînes en même temps sur la même base
    default_args={"retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["menuscan", "phase5"],
    doc_md=__doc__,
) as dag:
    verifier_sources = BashOperator(
        task_id="verifier_sources",
        bash_command=f'test -d "{RACINE}/menuscan_dataset/donnees_brutes" '
                     f'&& echo "Dossier donnees_brutes présent" '
                     f'|| (echo "Dossier menuscan_dataset/donnees_brutes introuvable" && exit 1)',
        retries=0,
        doc_md="Vérifie que les fichiers bruts sont là avant de lancer la chaîne.",
    )
    ingerer = BashOperator(
        task_id="ingerer",
        bash_command=commande("04_ingestion/ingerer.py"),
        doc_md="Charge dans raw les fichiers nouveaux ou modifiés ; les fichiers inchangés sont ignorés (journal SHA-256).",
    )
    controler_volumes = BashOperator(
        task_id="controler_volumes",
        bash_command=commande("04_ingestion/controler.py"),
        retries=0,                     # un écart de volume ne se corrige pas en relançant
        doc_md="Recompte chaque fichier et le compare au journal et à la base ; échoue au moindre écart.",
    )
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=commande("05_dbt/lancer_dbt.py", "build"),
        retries=0,                     # un test dbt en échec ne se corrige pas en relançant
        execution_timeout=timedelta(minutes=30),
        doc_md="Construit et teste l'entrepôt (staging, intermediate, marts, snapshot, 27 règles DQ).",
    )
    controler_entrepot = BashOperator(
        task_id="controler_entrepot",
        bash_command=commande("05_dbt/controler_entrepot.py"),
        doc_md="Compare l'entrepôt à la référence et écrit 05_dbt/rapport_validation.md.",
    )

    verifier_sources >> ingerer >> controler_volumes >> dbt_build >> controler_entrepot
