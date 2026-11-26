"""MenuScan TN - phase 5 (T5.2) : démonstration du chargement mois par mois.

    preparer_demo -> mois_2024_01 -> mois_2024_02 -> ... -> mois_2026_12 -> comparer_bases

1. preparer_demo : base menuscan_demo vide, dossier menuscan_dataset/demo_arrivees vide.
2. Une tâche par mois : elle lance le DAG menuscan_mois pour ce mois et attend sa fin. Les 36 exécutions de
   menuscan_mois apparaissent une par une dans l'interface, dans l'ordre des mois.
3. comparer_bases : la base de démonstration doit être identique à menuscan_dwh, chargé d'un coup.

Lancé à la main seulement (bouton ▶). Durée : environ 2 heures sur un portable (estimation).
Auteure : Sarra Abdeljaouad.
"""
import os

from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sdk import DAG

RACINE = os.environ.get("MENUSCAN_RACINE", "/opt/menuscan")
PYTHON = os.environ.get("MENUSCAN_PYTHON", "python")
MOIS = [f"{a}-{m:02d}" for a in (2024, 2025, 2026) for m in range(1, 13)]

with DAG(
    dag_id="menuscan_demo_36_mois",
    description="Démonstration : 36 mois livrés et traités un par un, puis comparaison avec menuscan_dwh",
    schedule=None,
    max_active_runs=1,
    is_paused_upon_creation=False,     # sans horaire : ne part jamais seul, actif pour pouvoir être lancé
    tags=["menuscan", "phase5", "demo"],
    doc_md=__doc__,
) as dag:
    precedente = BashOperator(
        task_id="preparer_demo",
        bash_command=f'cd "{RACINE}" && "{PYTHON}" 06_orchestration/demo/preparer_demo.py',
    )
    for mois in MOIS:
        tache = TriggerDagRunOperator(
            task_id=f"mois_{mois.replace('-', '_')}",
            trigger_dag_id="menuscan_mois",
            # run_after : heure du lancement (une exécution manuelle n'a pas de date logique dans Airflow 3)
            trigger_run_id=f"demo_{mois}__{{{{ dag_run.run_after.strftime('%Y%m%dT%H%M%S') }}}}",
            conf={"mois": mois},
            wait_for_completion=True,      # le mois suivant attend la fin de celui-ci
            poke_interval=15,
            failed_states=["failed"],
        )
        precedente >> tache
        precedente = tache
    comparer = BashOperator(
        task_id="comparer_bases",
        bash_command=f'cd "{RACINE}" && "{PYTHON}" 06_orchestration/demo/comparer_bases.py',
    )
    precedente >> comparer
