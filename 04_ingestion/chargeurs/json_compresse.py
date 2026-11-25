"""Journaux de tracking : une ligne JSON par événement, fichiers mensuels compressés en gzip, horodatage UTC,
libellés en anglais. Chaque ligne est gardée entière (colonne JSONB) ; une ligne illisible part dans raw.rejets."""
import gzip
import json


def lire_lignes(flux):
    for n, ligne in enumerate(flux, 1):
        ligne = ligne.rstrip("\n")
        if not ligne.strip():
            continue
        try:
            json.loads(ligne)
        except ValueError as err:
            yield n, None, f"JSON invalide : {err}", ligne
        else:
            yield n, [ligne]


def lire(chemin):
    return None, lire_lignes(gzip.open(chemin, "rt", encoding="utf-8"))
