# Historique des versions · 08_analyse_ml

## 0.3 (27/11/2026)

- T7.3 : `02_data_mining/01_regles_association` (EF-12) et `02_sensibilite_prix` (EF-11).
- Module `data_mining.py` : lift ajusté par établissement et test de Poisson ; élasticité par Poisson conditionnelle et bootstrap.
- `features.py` : `lignes_servies`, `versions_prix`, `panel_prix`.
- Run MLflow `retenu_test_2026` : paramètre `variables` ajouté, comme pour les candidats.
- README : procédure pour lancer et arrêter MLflow sous Windows.
- Preuve `04_livrables/machine_learning/P01_MLflow_comparaison_runs.png`.
- 12 tests (3 nouveaux sur `data_mining.py`).

## 0.2 (27/11/2026)

- T7.2 : `03_machine_learning/01_preparation_datasets_ml` (jeu figé et dictionnaire) et `02_prediction_resiliation` (K19).
- Modèle retenu sur la validation 2025 : régression logistique ; AUC 2026 = 0,794 [0,738 ; 0,850] ; J8 atteint en valeur centrale.
- Nouvelle variable `echeance_annuelle` : les résiliations en facturation annuelle tombent toutes juste avant l'échéance.
- Module `modeles.py` : variables, 3 facteurs par établissement, AUC par bootstrap, fiches. MLflow local (`config.experience_mlflow`).
- `features.panel(avec_mois_a_scorer=True)` ajoute décembre 2026, à scorer.
- EDA : libellé « commandes servies avec lignes de détail » (103 385 sur 103 431 ; écart de 46 à vérifier côté dbt).
- 9 tests automatiques (4 nouveaux sur `modeles.py`).

## 0.1 (27/11/2026)

- Arborescence alignée sur celle du projet TuniShop (étape 7), en minuscules comme le reste du dépôt.
- Module commun `00_commun/menuscan_analytics` : config, chargement, temporal_split, features.
- T7.1 : notebook `01_eda/01_eda_global` ; figures et tableaux dans `06_exports`.
- 5 tests automatiques (découpage temporel, fenêtres glissantes sans fuite).
