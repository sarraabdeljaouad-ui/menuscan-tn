# MenuScan TN · Analyses et machine learning (phase 7)

Autrice : Sarra Abdeljaouad · version 0.2 (27/11/2026)

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
| T7.2 | Risque de résiliation, K19 (EF-10) : AUC 2026 = 0,794 [0,738 ; 0,850] | Terminée |
| T7.3 | Règles d'association (EF-12), sensibilité au prix (EF-11) | À faire |
| T7.4 | Schéma `ml`, publication, décision J8 avec le sponsor | À faire |

## Résultat clé (test sur 2026, jamais vu à l'apprentissage)

| Cas | Modèle retenu | AUC 2026 | Intervalle à 95 % | Référence (règle simple) |
|---|---|---|---|---|
| Résiliation le mois suivant | Régression logistique, C = 0,03, classes pondérées | **0,794** | 0,738 à 0,850 | 0,668 (part de factures en retard) |

- Jalon J8 (AUC ≥ 0,75) atteint en valeur centrale ; la borne basse de l'intervalle est sous 0,75.
- Alerte (10 % les plus à risque chaque mois) : 14,7 % de vraies résiliations parmi les alertes, 48,7 % des résiliations repérées.
- Au 31/12/2026 : 265 établissements actifs scorés, 27 en alerte, 9,9 résiliations attendues en janvier 2027.

## Méthode

- Découpage temporel : apprentissage sur les résiliations de 2024 et 2025, test sur celles de 2026 (`temporal_split.py`).
- Pas de fuite : chaque variable n'utilise que des données antérieures ou égales à la fin du mois observé.
- Double sortie : chaque résultat est écrit en fichier (`06_exports`) et, à partir de T7.4, dans le schéma `ml`.
- Sécurité : le mot de passe est lu dans `.env`, jamais affiché ni écrit dans un notebook.

## Démarrer

1. Lire `00_ordre_execution.md`.
2. Installation, depuis la racine du dépôt : `pip install -r requirements.txt`.
3. Tests, depuis `08_analyse_ml` : `python -m pytest -q tests`.
4. Essais MLflow, depuis `08_analyse_ml` : `mlflow ui --backend-store-uri sqlite:///06_exports/journaux/mlflow.db`, puis http://127.0.0.1:5000.

## Arborescence

| Dossier | Contenu |
|---|---|
| `00_commun` | module `menuscan_analytics` (config, chargement, temporal_split, features, modeles), scripts SQL du schéma `ml` |
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
