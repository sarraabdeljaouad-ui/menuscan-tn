# MenuScan TN · Analyses et machine learning (phase 7)

Autrice : Sarra Abdeljaouad · version 0.3 (27/11/2026)

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
| T7.3 | Règles d'association (EF-12), sensibilité au prix (EF-11) | Terminée |
| T7.4 | Schéma `ml`, publication, décision J8 avec le sponsor | À faire |

## Résultat clé (test sur 2026, jamais vu à l'apprentissage)

| Cas | Modèle retenu | AUC 2026 | Intervalle à 95 % | Référence (règle simple) |
|---|---|---|---|---|
| Résiliation le mois suivant | Régression logistique, C = 0,03, classes pondérées | **0,794** | 0,738 à 0,850 | 0,668 (part de factures en retard) |

- Jalon J8 (AUC ≥ 0,75) atteint en valeur centrale ; la borne basse de l'intervalle est sous 0,75.
- Alerte (10 % les plus à risque chaque mois) : 14,7 % de vraies résiliations parmi les alertes, 48,7 % des résiliations repérées.
- Au 31/12/2026 : 265 établissements actifs scorés, 27 en alerte, 9,9 résiliations attendues en janvier 2027.

## Data mining (T7.3)

| Cas | Méthode | Résultat |
|---|---|---|
| Associations (EF-12) | Lift ajusté par établissement, test de Poisson corrigé (Bonferroni), apprentissage 2024-2025, vérification 2026 | 3 paires de catégories et 10 paires de plats retenues, toutes confirmées en 2026 ; 749 recommandations pour 55 établissements Pro |
| Sensibilité au prix (EF-11) | Poisson conditionnelle, effets fixes article et établissement × catégorie × mois, bootstrap par établissement, placebo | Élasticité globale -0,69 [-0,89 ; -0,47] ; placebo 0,01 [-0,36 ; 0,53] ; 6 catégories exploitables (dont 2 nettes : boissons chaudes, crêpes et gaufres), 14 non concluantes |

## Méthode

- Découpage temporel : apprentissage sur les résiliations de 2024 et 2025, test sur celles de 2026 (`temporal_split.py`).
- Pas de fuite : chaque variable n'utilise que des données antérieures ou égales à la fin du mois observé.
- Double sortie : chaque résultat est écrit en fichier (`06_exports`) et, à partir de T7.4, dans le schéma `ml`.
- Sécurité : le mot de passe est lu dans `.env`, jamais affiché ni écrit dans un notebook.

## Démarrer

1. Lire `00_ordre_execution.md`.
2. Installation, depuis la racine du dépôt : `pip install -r requirements.txt`.
3. Tests, depuis `08_analyse_ml` : `python -m pytest -q tests`.
4. Essais MLflow : voir la section « Consulter MLflow » ci-dessous.

## Consulter MLflow

1. Ouvrir une **nouvelle** fenêtre PowerShell, réservée à MLflow.
2. `cd <dossier du dépôt>\08_analyse_ml`
3. `..\.venv\Scripts\mlflow.exe ui --backend-store-uri sqlite:///06_exports/journaux/mlflow.db`
4. Attendre « Application startup complete », puis ouvrir http://127.0.0.1:5000, choisir « Model training », puis l'expérience `MenuScan_resiliation`.
5. Pour arrêter : **fermer la fenêtre**. Éviter Ctrl+C, qui peut faire passer PowerShell en mode débogage (dans ce cas : taper `q`, puis Entrée).

La commande doit être lancée depuis `08_analyse_ml` : le chemin de la base est relatif au dossier courant.

## Arborescence

| Dossier | Contenu |
|---|---|
| `00_commun` | module `menuscan_analytics` (config, chargement, temporal_split, features, modeles, data_mining), scripts SQL du schéma `ml` |
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
