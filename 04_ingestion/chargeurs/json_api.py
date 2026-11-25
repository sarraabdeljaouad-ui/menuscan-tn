"""Export de l'API de paiement : une ligne JSON par paiement (clés anglaises, montant imbriqué, horodatage UTC).
Même traitement que le tracking, sans compression."""
from .json_compresse import lire_lignes


def lire(chemin):
    return None, lire_lignes(open(chemin, encoding="utf-8"))
