"""Livre les fichiers d'un mois dans menuscan_dataset/demo_arrivees, comme s'ils arrivaient des systèmes sources.

    python livrer_mois.py 2024-03

- Fichiers mensuels (commandes, lignes de commande, événements) : ceux du mois demandé.
- Fichiers uniques (établissements, factures, prospects...) : livrés au premier mois, ce sont des extractions complètes
  (limite de la démonstration : le jeu de données ne les découpe pas par mois).
"""
import shutil
import sys

from commun import ARRIVEES, BRUTES, MOIS, SOURCES

mois = sys.argv[1]
if mois not in MOIS:
    sys.exit(f"Mois inconnu : {mois} (attendu AAAA-MM, de {MOIS[0]} à {MOIS[-1]})")
suffixe = mois.replace("-", "_")
livres = []
for motif, _table, _fmt in SOURCES:
    for f in sorted(BRUTES.glob(motif)):
        mensuel = "*" in motif
        if (mensuel and suffixe in f.name) or (not mensuel and mois == MOIS[0]):
            cible = ARRIVEES / f.relative_to(BRUTES)
            cible.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, cible)
            livres.append(str(f.relative_to(BRUTES)).replace("\\", "/"))
if not livres:
    sys.exit(f"Aucun fichier trouvé pour {mois} dans {BRUTES}")
print(f"Mois {mois} : {len(livres)} fichier(s) livré(s)")
for nom in livres:
    print(f"  {nom}")
