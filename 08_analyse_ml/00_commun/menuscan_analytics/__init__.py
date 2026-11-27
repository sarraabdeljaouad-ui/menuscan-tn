"""menuscan_analytics : module commun à l'EDA, au data mining et au machine learning de MenuScan TN.

Autrice : Sarra Abdeljaouad

Pourquoi un module commun ?
    Tous les notebooks lisent les mêmes données, avec les mêmes règles et les mêmes variables,
    construites par le même code. Un modèle ne peut donc pas utiliser une variable calculée
    autrement que ce que montre l'EDA.

Fichiers :
    config.py          dossiers, date d'arrêté, style des graphiques, enregistrement des figures et tableaux
    chargement.py      connexion à l'entrepôt PostgreSQL (mot de passe lu dans .env, jamais affiché)
    temporal_split.py  découpage apprentissage / test
    features.py        tables de variables (jeu mensuel des établissements)

Utilisation dans un notebook (le notebook est dans 01_eda/, 02_data_mining/ ou 03_machine_learning/) :
    import sys; sys.path.insert(0, "../00_commun")
    from menuscan_analytics import config, chargement, temporal_split, features
"""
__version__ = "0.1"
