# 03_generateur : jeu de démonstration (phase 2)

**Auteure :** Sarra Abdeljaouad · **Date :** 25/11/2026 · **Tâche :** T2.2

Ce dossier contient un **jeu de démonstration** au format Parquet, pour essayer le projet sans télécharger le jeu complet (Release `v1.1-donnees`, 66,8 Mo). Le code du générateur y sera ajouté en phase 9 (décision D-30) : il contient les réponses que le dossier `solutions/` garde cachées.

## Contenu

- `demo_data/` : 20 tables au format Parquet (compression zstd), 75 994 lignes, 1,3 Mo.
- `demo_data/manifeste.json` : établissements retenus, formule de chacun, nombre de lignes et empreinte SHA-256 de chaque fichier.
- `creer_demo.py` : le script qui extrait la démonstration du jeu complet. Il est déterministe : relancé, il redonne les mêmes fichiers.

| Table | Lignes |
|---|---|
| `abonnements` | 23 |
| `articles` | 527 |
| `articles_prix_historique` | 736 |
| `campagnes_marketing` | 134 |
| `canaux_acquisition` | 5 |
| `categories_menu` | 135 |
| `commandes` | 3 919 |
| `dim_calendrier` | 1 096 |
| `etablissements` | 20 |
| `evenements` | 49 995 |
| `factures` | 254 |
| `formules` | 3 |
| `lignes_commande` | 8 814 |
| `marketing_depenses_quotidiennes` | 548 |
| `paiements` | 260 |
| `prospects` | 358 |
| `ref_villes` | 8 |
| `sessions` | 8 717 |
| `tables_salle` | 367 |
| `tickets_support` | 75 |
| **Total** | **75 994** |

## Règles de découpage

- **20 établissements** tirés au sort (graine 2027) parmi les 250 abonnés entre janvier et juin 2026 : 7 en formule Essentiel, 8 en Commande, 5 en Pro (formule au 01/04/2026). ETB0005, le Café Les Arcades utilisé dans l'application, en fait partie. Le jeu compte 3 signatures et 3 résiliations pendant la période, 6 villes et 4 types d'établissement.
- **Activité du 01/01/2026 au 30/06/2026** (sessions, événements, commandes, lignes, dépenses marketing). La période couvre le Ramadan 2026.
- **Historique complet** des abonnements, factures, paiements, tickets, menus, prix et tables de ces 20 établissements. Les colonnes d'état des établissements (statut, formule actuelle, résiliation) sont une photo au 31/12/2026, comme dans le jeu complet.
- **Complets :** calendrier, villes, formules, canaux et campagnes.
- **Prospects :** ceux convertis en l'un des 20 établissements, et les prospects non convertis contactés pendant la période. Un parrain hors de la démonstration est mis à vide (1 cas).

## Vérifications

- Les 20 tables se chargent dans PostgreSQL avec **toutes les clés étrangères actives**, y compris les deux clés circulaires entre prospects et établissements.
- Les **23 contrôles qualité** de `02_oltp/controles_qualite.sql` donnent **0 violation**.
- Chaque colonne garde le type du schéma `02_oltp/schema_postgres.sql` : un entier reste un entier même avec des cases vides, une date reste une date.

## Utiliser la démonstration

```python
import pandas as pd
commandes = pd.read_parquet("03_generateur/demo_data/commandes.parquet")
```

DuckDB lit les fichiers directement (`SELECT * FROM '03_generateur/demo_data/commandes.parquet'`), et Power BI Desktop aussi (Obtenir les données, Parquet).

## Régénérer la démonstration

Après avoir décompressé le jeu complet à la racine du dépôt :

```powershell
python 03_generateur/creer_demo.py --source menuscan_dataset/donnees_reference
```

## Limites

- C'est un extrait de la **couche de référence** (données propres). La couche brute, avec ses anomalies, n'existe que dans le jeu complet : la phase 3 (ingestion) s'en sert.
- Les données créées par l'application (appels, avis, encaissements) ne sont pas dans la démonstration : elles vivent dans la base applicative.
