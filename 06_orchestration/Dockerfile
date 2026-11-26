# Image Airflow de MenuScan TN : Airflow 3.3.2 (décision D-36) + un environnement Python séparé pour nos scripts.
# Airflow et dbt ont chacun leurs dépendances ; les mettre dans le même environnement crée des conflits de versions.
# Les tâches du DAG lancent donc nos scripts avec /opt/menuscan_venv/bin/python, Airflow ne fait que les enchaîner.
FROM apache/airflow:3.3.2

USER airflow
RUN python -m venv /opt/airflow/menuscan_venv \
 && /opt/airflow/menuscan_venv/bin/pip install --no-cache-dir \
      "dbt-core==1.12.7" "dbt-postgres==1.11.0" pandas pyarrow sqlalchemy psycopg2-binary
ENV MENUSCAN_PYTHON=/opt/airflow/menuscan_venv/bin/python \
    MENUSCAN_RACINE=/opt/menuscan
