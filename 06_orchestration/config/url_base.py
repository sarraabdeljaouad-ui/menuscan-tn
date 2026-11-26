"""Adresse de la base de métadonnées d'Airflow, construite depuis les variables POSTGRES_* du fichier .env.
Le mot de passe est encodé : il peut contenir @, !, : ou / (lu par AIRFLOW__DATABASE__SQL_ALCHEMY_CONN_CMD)."""
import os
from urllib.parse import quote_plus

# end="" : pas de saut de ligne final, sinon Airflow cherche une base nommée « airflow\n »
print("postgresql+psycopg2://{}:{}@postgres:5432/airflow".format(
    quote_plus(os.environ["POSTGRES_USER"]), quote_plus(os.environ["POSTGRES_PASSWORD"])), end="")
