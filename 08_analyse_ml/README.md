# MenuScan TN · Analyses et machine learning (phase 7)

Autrice : Sarra Abdeljaouad · version 0.1 (27/11/2026)

MenuScan TN est une start-up **fictive** ; toutes les données sont **synthétiques**.
Cette phase transforme l'entrepôt (`menuscan_dwh`, schéma `marts`, construit par dbt) en décisions mesurées :
exploration, data mining, modèle de risque de résiliation, publication des résultats pour Power BI.

```
Entrepôt menuscan_dwh (schéma marts, dbt)
            │
            ▼
Notebooks Python (EDA ▸ data mining ▸ machine learning)
            │                         │
            ▼                         ▼
06_exports (CSV, PNG, modèles)   schéma ml de l'entrepôt (T7.4)
                                      │
                                      ▼
                         Power BI (07_powerbi, à la racine du dépôt)
```

## Avancement

| Tâche | Contenu | Statut |
|---|---|---|
| T7.1 | EDA globale : résiliations, signaux d'usage, paniers, prix | Terminée |
| T7.2 | Risque de résiliation, K19 (EF-10) | À faire |
| T7.3 | Règles d'association (EF-12), sensibilité au prix (EF-11) | À faire |
| T7.4 | Suivi MLflow local, schéma `ml`, décision J8 (AUC ≥ 0,75 sur 2026) | À faire |

## Méthode

- Découpage temporel : apprentissage sur les résiliations de 2024 et 2025, test sur celles de 2026 (`temporal_split.py`).
- Pas de fuite : chaque variable n'utilise que des données antérieures ou égales à la fin du mois observé.
- Double sortie : chaque résultat est écrit en fichier (`06_exports`) et, à partir de T7.4, dans le schéma `ml`.
- Sécurité : le mot de passe est lu dans `.env`, jamais affiché ni écrit dans un notebook.

## Démarrer

1. Lire `00_ordre_execution.md`.
2. Installation, depuis la racine du dépôt : `pip install -r requirements.txt`.
3. Tests, depuis `08_analyse_ml` : `python -m pytest -q tests`.

## Arborescence

| Dossier | Contenu |
|---|---|
| `00_commun` | module `menuscan_analytics` (config, chargement, temporal_split, features), scripts SQL du schéma `ml` |
| `01_eda` | notebooks d'exploration |
| `02_data_mining` | règles d'association, sensibilité au prix |
| `03_machine_learning` | préparation, modèle de résiliation, évaluation, scores, publication |
| `04_livrables` | rapports par sous-phase et documents d'exploitation (fiches modèles) |
| `05_data` | tables de variables (hors Git), dictionnaire et lignage |
| `06_exports` | figures, tableaux, modèles et fiches, prédictions, journaux |
| `tests` | tests automatiques (sans base de données) |

Le projet Power BI reste dans `07_powerbi`, à la racine du dépôt : un seul modèle sémantique pour toutes les phases.
Les PV de validation vont dans `09_recette`, à la racine du dépôt.

## Précaution

Les liens observés reproduisent les règles du générateur de données. Une bonne mesure prouve que la méthode
retrouve ces règles, pas qu'elle marcherait telle quelle sur de vrais clients.
