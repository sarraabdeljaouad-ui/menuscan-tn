"""Remet la démonstration à zéro : base menuscan_demo vide, dossier menuscan_dataset/demo_arrivees vide.
L'entrepôt menuscan_dwh n'est pas touché."""
import shutil

from commun import ARRIVEES, BASE_DEMO, connexion

conn = connexion("menuscan_app")
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()", (BASE_DEMO,))
    cur.execute(f"DROP DATABASE IF EXISTS {BASE_DEMO}")
    cur.execute(f"CREATE DATABASE {BASE_DEMO}")
conn.close()
shutil.rmtree(ARRIVEES, ignore_errors=True)
ARRIVEES.mkdir(parents=True)
print(f"Base {BASE_DEMO} recréée vide ; dossier {ARRIVEES.name} vidé.")
