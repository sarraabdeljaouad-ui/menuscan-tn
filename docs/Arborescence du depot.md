# Arborescence du dépôt

**Référence :** MS-DATA-ARB-001 · **Version :** 1.3 · **Date :** 23/11/2026 · **Auteure :** Sarra Abdeljaouad

Le dépôt `menuscan-tn` suit les phases du projet : un dossier numéroté par phase, dans l'ordre de réalisation. Les dossiers des phases à venir sont créés au démarrage de chaque phase.

## Vue d'ensemble

```
menuscan-tn/
├── README.md                     ← présentation du projet (page d'accueil GitHub)
├── LICENSE                       ← licence MIT
├── .gitignore                    ← fichiers exclus du dépôt
├── requirements.txt              ← bibliothèques Python
├── docker-compose.yml            ← PostgreSQL, puis Airflow (phase 5)
├── .env.example                  ← modèle des variables d'environnement (sans mot de passe réel)
├── outils/verifier_poste.py      ← vérification du poste de travail (réserve RV-02)
│
├── 00_cadrage/                   ← phase 0
│   ├── 1-Cadrage et besoins métier/        (6 documents Word)
│   ├── 2-Organisation et pilotage/         (plan de management, registre, classeur)
│   ├── 3-Analyse des données sources/      (notebook, cartographie, audit, plan d'intégration)
│   ├── 4-Gouvernance des données/          (référentiel, qualité, modélisation, modèles)
│   └── 6-Validation de la phase 0/         (recette, rapport, PV)
│
├── 01_application/               ← phase 1 : deux applications Streamlit
│   ├── commun/                   (db.py, theme.py : accès aux données et thème partagés)
│   ├── client/                   (application client ouverte par QR code, port 8501)
│   ├── equipe/                   (application équipe avec connexion gérant et serveur, port 8502)
│   ├── qr/                       (generer_qr.py ; sortie/ exclu de Git)
│   └── README.md
│
├── 02_oltp/                      ← phase 1 : base applicative
│   ├── schema_postgres.sql
│   ├── charger_base_app.py
│   ├── migrations/               (évolutions du modèle : 001 parcours de commande, 002 comptes de l'équipe, 003 état conservé après actualisation, 004 service en salle)
│   ├── controles_qualite.sql
│   └── diagramme_er.png
│
├── 03_generateur/                ← phase 2 : génération des données
│   ├── gen_part1.py … gen_part5_export.py
│   ├── generer_menuscan.py
│   ├── meta.py
│   └── demo_data/                (jeu de démonstration en Parquet)
│
├── 04_ingestion/                 ← phase 3 : chargement de la couche brute
│   ├── chargeurs/                (CSV, CSV français, JSON compressé, JSON d'API)
│   ├── journal.sql               (table raw.chargements)
│   └── ingerer.py
│
├── 05_dbt/                       ← phase 4 : projet dbt
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── staging/              (stg_*)
│   │   ├── intermediate/         (int_*)
│   │   └── marts/                (fait_*, dim_*)
│   ├── seeds/                    (tables de correspondance des libellés)
│   ├── snapshots/
│   ├── tests/                    (tests DQ spécifiques)
│   └── macros/
│
├── 06_orchestration/             ← phase 5 : Airflow
│   └── dags/menuscan_chaine_complete.py
│
├── 07_powerbi/                   ← phase 6 : rapports au format .pbip
│   ├── MenuScan_Startup.pbip
│   └── MenuScan_Etablissement.pbip
│
├── 08_analyse_ml/                ← phases 7 et 8 : notebooks et modèles
│   ├── 01_eda.ipynb
│   ├── 02_resiliation.ipynb
│   ├── 03_sensibilite_prix.ipynb
│   ├── 04_recommandations.ipynb
│   └── fiches_modeles/
│
├── 09_recette/                   ← notes de validation et PV des phases 1 à 9
│
└── docs/                         ← documents transverses
    ├── Presentation du projet.md
    ├── Installation du poste de travail.md
    ├── Conventions de nommage et de codage.md
    ├── Arborescence du depot.md
    ├── captures/                 (captures des rapports et de l'application)
    └── MenuScan_Synthese.pdf     (synthèse d'une page, phase 9)
```

## Ce qui n'est pas dans le dépôt

| Élément | Raison | Où le trouver |
|---|---|---|
| Jeu de données complet (284 Mo) | Taille du dépôt | ZIP dans la page Releases (décision D-15) |
| Dossier `solutions/` du jeu de données | Garder la démarche de nettoyage crédible (décision D-16, comme pour TuniShop) | Conservé en local |
| Fichier `.env` | Contient les mots de passe locaux | Créé à partir de `.env.example` |
| Environnement Python `.venv/` | Recréé par `pip install -r requirements.txt` | – |
| Sorties de dbt (`target/`, `logs/`) et d'Airflow | Régénérées à chaque exécution | – |
| Fichiers temporaires de Power BI | Régénérés par Power BI Desktop | – |

## Contenu du fichier .gitignore

```
# Python
.venv/
__pycache__/
*.pyc
.ipynb_checkpoints/

# Secrets
.env

# Données lourdes ou sensibles
menuscan_dataset/
solutions/
*.sqlite

# dbt
05_dbt/target/
05_dbt/logs/
05_dbt/dbt_packages/

# Airflow
06_orchestration/logs/

# MLflow
mlruns/

# Power BI (fichiers locaux)
**/.pbi/localSettings.json
**/.pbi/cache.abf

# Système
.DS_Store
Thumbs.db
```

## Correspondance avec la documentation de la phase 0

Le dossier `00_cadrage/` reprend l'arborescence de la phase 0. Le dossier 5 (Environnement et dépôt) n'y est pas recopié : ses fichiers sont placés à la racine (`README.md`) et dans `docs/`.
