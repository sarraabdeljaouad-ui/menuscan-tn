"""Chargeurs de la couche brute : chacun lit un format et renvoie les enregistrements tels qu'ils sont, sans conversion.

Chaque chargeur expose lire(chemin) -> (colonnes, enregistrements) :
- colonnes : liste des noms de colonnes (None pour le JSON, stocké entier dans une colonne JSONB) ;
- enregistrements : itérateur de (numéro de ligne dans le fichier, valeurs) ou (numéro, None, motif, contenu) pour un rejet.
"""
from . import csv_francais, csv_standard, json_api, json_compresse

PAR_FORMAT = {"csv": csv_standard, "csv_fr": csv_francais, "json_gz": json_compresse, "json_api": json_api}
