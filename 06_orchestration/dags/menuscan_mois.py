"""MenuScan TN - phase 5 (T5.2) : traitement d'un mois livré, dans la base de démonstration menuscan_demo.

    livrer_fichiers -> ingerer -> controler_volumes -> dbt_build

Lancé par menuscan_demo_36_mois, un mois après l'autre (paramètre « mois », au format AAAA-MM).
Les mêmes scripts que la chaîne quotidienne, dirigés vers menuscan_demo (variable MENUSCAN_DWH) ;
l'entrepôt menuscan_dwh n'est pas touché.
Mois 1 à 35 : un test dbt en échec est un avertissement (données encore en transit, par exemple une commande
dont les événements arrivent le mois suivant). Dernier mois : tests bloquants, comme dans la chaîne quotidienne.
Auteure : Sarra Abdeljaouad.
"""
import os

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG, Param

RACINE = os.environ.get("MENUSCAN_RACINE", "/opt/menuscan")
PYTHON = os.environ.get("MENUSCAN_PYTHON", "python")
DERNIER_MOIS = "2026-12"
ENV = {"MENUSCAN_DWH": "menuscan_demo"}      # ajouté aux variables du conteneur (append_env)
ARRIVEES = "menuscan_dataset/demo_arrivees"


def commande(script, *arguments):
    return f'cd "{RACINE}" && "{PYTHON}" {script} {" ".join(arguments)}'.strip()


with DAG(
    dag_id="menuscan_mois",
    description="Démonstration : livraison et traitement d'un mois dans menuscan_demo",
    schedule=None,                     # lancé seulement par menuscan_demo_36_mois (ou à la main)
    max_active_runs=1,
    is_paused_upon_creation=False,     # sans horaire : ne part jamais seul, actif pour pouvoir être lancé
    params={"mois": Param("2024-01", type="string", pattern=r"^20(24|25|26)-(0[1-9]|1[0-2])$",
                          description="Mois livré, au format AAAA-MM")},
    tags=["menuscan", "phase5", "demo"],
    doc_md=__doc__,
) as dag:
    livrer = BashOperator(
        task_id="livrer_fichiers",
        bash_command=commande("06_orchestration/demo/livrer_mois.py", "{{ params.mois }}"),
        doc_md="Copie dans menuscan_dataset/demo_arrivees les fichiers du mois (et les fichiers uniques au premier mois).",
    )
    ingerer = BashOperator(
        task_id="ingerer",
        bash_command=commande("04_ingestion/ingerer.py", "--source", ARRIVEES),
        env=ENV, append_env=True,
    )
    controler_volumes = BashOperator(
        task_id="controler_volumes",
        bash_command=commande("04_ingestion/controler.py", "--source", ARRIVEES, "--reference", "absent",
                              "--rapport", "menuscan_dataset/demo_rapport_ingestion.md"),
        env=ENV, append_env=True,
    )
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=commande("05_dbt/lancer_dbt.py", "build", "--target-path", "target_demo", "--vars",
                              "\"{severite_tests: {{ 'error' if params.mois == '" + DERNIER_MOIS + "' else 'warn' }}}\""),
        env=ENV, append_env=True,
    )
    livrer >> ingerer >> controler_volumes >> dbt_build
