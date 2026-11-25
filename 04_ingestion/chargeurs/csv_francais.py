"""CSV au format français (logiciel comptable, outil marketing) : séparateur point-virgule, virgule décimale,
dates JJ/MM/AAAA. Les valeurs restent du texte (« 150,0 », « 03/01/2024 ») : la conversion se fait en phase 4 (dbt)."""
from . import csv_standard

SEPARATEUR = ";"


def lire(chemin):
    return csv_standard.lire(chemin, SEPARATEUR)
