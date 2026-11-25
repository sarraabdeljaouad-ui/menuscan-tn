"""CSV des systèmes sources (séparateur virgule, UTF-8, première ligne = en-tête). Aucune valeur n'est convertie."""
import csv

SEPARATEUR = ","


def lire(chemin, separateur=SEPARATEUR):
    f = open(chemin, encoding="utf-8", newline="")
    lecteur = csv.reader(f, delimiter=separateur)
    colonnes = next(lecteur)

    def enregistrements():
        with f:
            for valeurs in lecteur:
                n = lecteur.line_num  # numéro de la dernière ligne physique lue
                if not valeurs:
                    continue
                if len(valeurs) != len(colonnes):
                    yield n, None, f"{len(valeurs)} colonnes au lieu de {len(colonnes)}", separateur.join(valeurs)
                else:
                    yield n, valeurs
    return colonnes, enregistrements()
