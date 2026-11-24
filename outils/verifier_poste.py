# -*- coding: utf-8 -*-
"""Vérifie que le poste de travail est prêt pour le projet MenuScan TN.

Usage, depuis la racine du dépôt, environnement Python activé :
    python outils/verifier_poste.py

Reprend les contrôles de la section 8 de docs/Installation du poste de travail.md.
Ne modifie rien : il lit, exécute des commandes de version et se connecte aux bases.
"""
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
BIBLIOS = ["pandas", "numpy", "pyarrow", "sqlalchemy", "psycopg2", "streamlit", "qrcode",
           "sklearn", "statsmodels", "mlxtend", "mlflow", "matplotlib"]
resultats = []


def note(controle, ok, detail):
    resultats.append((controle, "OK" if ok else "KO", detail))


def cmd(args):
    """Exécute une commande ; renvoie (code, sortie) sans lever d'exception."""
    if shutil.which(args[0]) is None:
        return None, f"{args[0]} introuvable"
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=RACINE)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def lire_env():
    f = RACINE / ".env"
    if not f.exists():
        return None
    env = {}
    for ligne in f.read_text(encoding="utf-8").splitlines():
        if "=" in ligne and not ligne.strip().startswith("#"):
            k, v = ligne.split("=", 1)
            env[k.strip()] = v.strip()
    return env


# 1. Python
v = sys.version_info
note("Python 3.11 ou plus", v >= (3, 11), f"{v.major}.{v.minor}.{v.micro}")
note("Environnement virtuel actif", sys.prefix != sys.base_prefix, sys.prefix)

# 2. Bibliothèques
manquantes = []
for b in BIBLIOS:
    try:
        importlib.import_module(b)
    except Exception:  # noqa: BLE001
        manquantes.append(b)
note("Bibliothèques Python", not manquantes, "toutes présentes" if not manquantes else "manquantes : " + ", ".join(manquantes))

# 3. Outils en ligne de commande
for nom, args in [("Git", ["git", "--version"]), ("dbt", ["dbt", "--version"]), ("Docker", ["docker", "--version"])]:
    code, out = cmd(args)
    note(nom, code == 0, out.splitlines()[0] if out else "")

# 4. Fichier .env
env = lire_env()
if env is None:
    note("Fichier .env", False, "absent : copier .env.example en .env")
else:
    defaut = env.get("POSTGRES_PASSWORD") in (None, "", "choisir_un_mot_de_passe")
    note("Fichier .env", not defaut, "mot de passe à changer" if defaut else "présent")

# 5. Conteneur PostgreSQL
code, out = cmd(["docker", "ps", "--filter", "name=menuscan_postgres", "--format", "{{.Status}}"])
note("Conteneur menuscan_postgres", code == 0 and out.startswith("Up"), out or "non démarré : docker compose up -d")

# 6. Connexion aux deux bases
if env:
    try:
        import psycopg2
        for base in ("menuscan_app", "menuscan_dwh"):
            try:
                c = psycopg2.connect(host="localhost", port=env.get("POSTGRES_PORT", "5432"), user=env.get("POSTGRES_USER"),
                                     password=env.get("POSTGRES_PASSWORD"), dbname=base, connect_timeout=5)
                cur = c.cursor(); cur.execute("SHOW server_version"); ver = cur.fetchone()[0]; c.close()
                note(f"Base {base}", True, f"PostgreSQL {ver}")
            except Exception as e:  # noqa: BLE001
                note(f"Base {base}", False, str(e).strip().splitlines()[0])
    except ImportError:
        note("Bases PostgreSQL", False, "psycopg2 absent")

# 7. Git : rien de sensible suivi
code, out = cmd(["git", "ls-files"])
if code == 0:
    sensibles = [f for f in out.splitlines() if f == ".env" or f.startswith(("menuscan_dataset/", ".venv/")) or "/solutions/" in f or f.startswith("solutions/")]
    note("Git : aucun fichier sensible suivi", not sensibles, "aucun" if not sensibles else ", ".join(sensibles[:5]))
else:
    note("Git : aucun fichier sensible suivi", False, "pas un dépôt Git")

# Affichage
larg = max(len(r[0]) for r in resultats)
print()
for c, s, d in resultats:
    print(f"  {s:2}  {c.ljust(larg)}  {d}")
n = sum(r[1] == "OK" for r in resultats)
print(f"\n  {n} contrôles réussis sur {len(resultats)}.")
sys.exit(0 if n == len(resultats) else 1)
