# 00_commun

| Élément | Contenu |
|---|---|
| `menuscan_analytics/config.py` | dossiers, date d'arrêté, style, enregistrement des figures et tableaux |
| `menuscan_analytics/chargement.py` | connexion à `menuscan_dwh` (identifiants lus dans `.env`), fonction `lire()` |
| `menuscan_analytics/temporal_split.py` | découpage apprentissage (2024-2025) / test (2026) |
| `menuscan_analytics/features.py` | `panel()` : une ligne par établissement actif et par mois, avec la cible de résiliation |
| `sql/` | scripts du schéma `ml` (T7.4, à venir) |

Les dépendances sont dans `requirements.txt`, à la racine du dépôt.

Utilisation dans un notebook :

```python
import sys; sys.path.insert(0, "../00_commun")
from menuscan_analytics import chargement, config, features, temporal_split
```
