# -*- coding: utf-8 -*-
"""Génère les QR codes d'un établissement : un PNG par table et la planche PDF à imprimer.

Usage, depuis la racine du dépôt, environnement Python activé :
    python 01_application/qr/generer_qr.py ETB0005
    python 01_application/qr/generer_qr.py ETB0005 --url http://192.168.1.222:8501

Sans --url, l'adresse est CLIENT_URL du fichier .env (par défaut http://localhost:8501).
Les fichiers sont écrits dans 01_application/qr/sortie/<établissement>/ (dossier exclu de Git).
"""
import argparse
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent))
from commun import db, qr  # noqa: E402

p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
p.add_argument("etablissement", help="identifiant de l'établissement, par exemple ETB0005")
p.add_argument("--url", help="adresse de l'application client")
a = p.parse_args()
etab = a.etablissement.upper()
base = (a.url or db.url_client()).rstrip("/")
info = db.un("SELECT nom_etablissement FROM etablissements WHERE etablissement_id = :e", e=etab)
if not info:
    sys.exit(f"Établissement inconnu : {etab}")
tables = db.lire("SELECT table_id, numero_table, zone FROM tables_salle WHERE etablissement_id = :e ORDER BY numero_table", e=etab)
sortie = ICI / "sortie" / etab
sortie.mkdir(parents=True, exist_ok=True)
for t in tables:
    (sortie / f"QR_{t['table_id']}_table{t['numero_table']}.png").write_bytes(qr.png(qr.url_table(base, t["table_id"]), 1000))
(sortie / f"QR_{etab}_planche.pdf").write_bytes(qr.planche_pdf(info["nom_etablissement"], tables, base))
print(f"{len(tables)} QR codes et 1 planche PDF pour {info['nom_etablissement']} dans {sortie}")
print(f"Adresse encodée : {base}/?table=...")
