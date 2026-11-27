# MenuScan TN · Phase 7 : ordre d'exécution (version 0.2)

Autrice : Sarra Abdeljaouad · Suis les numéros dans l'ordre. Chaque étape a besoin de la précédente.

## A. Préparation (une seule fois)

| N° | Où | Action | Résultat attendu |
|---|---|---|---|
| 1 | Terminal, racine du dépôt, venv activé | `pip install -r requirements.txt` | bibliothèques installées |
| 2 | Docker Desktop | `docker compose up -d postgres` | PostgreSQL sur le port 5440 |
| 3 | Terminal, `05_dbt` | `python lancer_dbt.py build` | entrepôt à jour (schéma `marts`) |

## B. Analyse (notebooks, « Exécuter tout »)

| N° | Dossier | Notebook | Produit |
|---|---|---|---|
| 4 | `01_eda` | `01_eda_global` | jeu mensuel, signaux de résiliation, paniers, prix ; figures et tableaux `EDA01_*` |
| 5 | `03_machine_learning` | `01_preparation_datasets_ml` | `05_data/features/etablissement_mois.parquet` (4 431 lignes) et son dictionnaire |
| 6 | `03_machine_learning` | `02_prediction_resiliation` | modèle K19, mesures 2026, scores au 31/12/2026, fiche, runs MLflow |
| 7 | `02_data_mining` | `01_regles_association` | à venir (T7.3) |
| 8 | `02_data_mining` | `02_sensibilite_prix` | à venir (T7.3) |
| 9 | `03_machine_learning` | `03_evaluation_modeles` | à venir (T7.4) |
| 10 | `03_machine_learning` | `04_publication_resultats` | à venir (T7.4), en dernier |

## C. Contrôles

| N° | Où | Action | Résultat attendu |
|---|---|---|---|
| 11 | Terminal, `08_analyse_ml` | `python -m pytest -q tests` | tous les tests passent |
