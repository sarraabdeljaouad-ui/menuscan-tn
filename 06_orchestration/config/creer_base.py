"""Crée la base « airflow » dans le conteneur PostgreSQL du projet si elle n'existe pas encore.
Lancé une fois par le service airflow-init, avant « airflow db migrate »."""
import os
import time

import psycopg2

for essai in range(30):  # PostgreSQL peut mettre quelques secondes à démarrer
    try:
        conn = psycopg2.connect(host="postgres", port=5432, dbname="menuscan_app",
                                user=os.environ["POSTGRES_USER"], password=os.environ["POSTGRES_PASSWORD"])
        break
    except psycopg2.OperationalError:
        time.sleep(2)
else:
    raise SystemExit("PostgreSQL ne répond pas : lancer d'abord docker compose up -d")
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'airflow'")
    if cur.fetchone():
        print("Base airflow : déjà présente")
    else:
        cur.execute("CREATE DATABASE airflow")
        print("Base airflow : créée")
conn.close()
