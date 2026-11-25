# -*- coding: utf-8 -*-
"""Lance dbt avec la connexion du fichier .env, depuis n'importe quel dossier du dépôt.

    python 05_dbt/lancer_dbt.py debug     # vérifier la connexion
    python 05_dbt/lancer_dbt.py build     # tout construire et tester

Tout ce qui suit lancer_dbt.py est passé à dbt tel quel (par exemple : run --select stg_commandes).
"""
import os
import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent


def charger_env():
    fichier = RACINE / ".env"
    if not fichier.exists():
        sys.exit(f"Fichier introuvable : {fichier}. Le créer à partir de .env.example.")
    for ligne in fichier.read_text(encoding="utf-8").splitlines():
        if "=" in ligne and not ligne.strip().startswith("#"):
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip())


def main():
    charger_env()
    from dbt.cli.main import dbtRunner  # importé après le .env : dbt lit les variables au démarrage

    arguments = sys.argv[1:] or ["--help"]
    if arguments[0] not in ("--help", "-h", "--version"):
        arguments += ["--project-dir", str(DOSSIER), "--profiles-dir", str(DOSSIER)]
    os.chdir(DOSSIER)
    resultat = dbtRunner().invoke(arguments)
    sys.exit(0 if resultat.success else 1)


if __name__ == "__main__":
    main()
