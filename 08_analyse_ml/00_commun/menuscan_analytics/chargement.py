"""chargement.py : connexion à l'entrepôt PostgreSQL et lecture de requêtes.

Le mot de passe est lu dans le fichier .env du dépôt (jamais affiché, jamais écrit ailleurs).
La base cible suit MENUSCAN_DWH (défaut menuscan_dwh), comme l'ingestion.
"""
from __future__ import annotations

import sys
from functools import lru_cache

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from . import config

sys.path.insert(0, str(config.DEPOT / "04_ingestion"))
from ingerer import lire_env, nom_base  # noqa: E402


@lru_cache(maxsize=1)
def moteur():
    e = lire_env()
    url = URL.create("postgresql+psycopg2", username=e["POSTGRES_USER"], password=e["POSTGRES_PASSWORD"],
                     host=e.get("POSTGRES_HOST", "localhost"), port=int(e.get("POSTGRES_PORT", "5440")),
                     database=nom_base())
    return create_engine(url)


def lire(sql: str, **params) -> pd.DataFrame:
    """Exécute une requête SELECT et renvoie un DataFrame."""
    with moteur().connect() as c:
        return pd.read_sql_query(sql, c, params=params or None)
