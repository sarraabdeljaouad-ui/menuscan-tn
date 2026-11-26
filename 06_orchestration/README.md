# 06_orchestration : chaîne automatisée avec Airflow (phase 5)

**Auteure :** Sarra Abdeljaouad · **Date :** 26/11/2026 · **Tâches :** T5.1 (chaîne quotidienne), T5.2 (démonstration mois par mois) · **Outil :** Apache Airflow 3.3.2 (décision D-36)

## 1. Ce que fait Airflow ici

Jusqu'à la phase 4, la chaîne se lançait à la main, en 4 commandes et dans cet ordre. Airflow les lance à ta place, dans le même ordre, et s'arrête à la première erreur :

```
verifier_sources  →  ingerer  →  controler_volumes  →  dbt_build  →  controler_entrepot
```

| Tâche | Commande lancée (depuis la racine du dépôt) | Échoue si |
|---|---|---|
| `verifier_sources` | vérifie que `menuscan_dataset/donnees_brutes` existe | le dossier manque |
| `ingerer` | `python 04_ingestion/ingerer.py` | un fichier ne se charge pas |
| `controler_volumes` | `python 04_ingestion/controler.py` | un volume ne correspond pas |
| `dbt_build` | `python 05_dbt/lancer_dbt.py build` | un modèle ou un test dbt échoue |
| `controler_entrepot` | `python 05_dbt/controler_entrepot.py` | le script plante |

Le DAG (le fichier qui décrit la chaîne) est `dags/menuscan_chaine_complete.py`. Il n'ajoute aucun traitement : il appelle les mêmes scripts que toi. Il tourne **tous les jours à minuit, heure de Tunis**, et peut aussi être lancé à la main. Minuit laisse environ 25 minutes de marge après la chaîne TuniShop (22 h, 1 h 34 au plus sur l'historique de SQL Server Agent).

**Vocabulaire :**

| Mot | Sens |
|---|---|
| **DAG** | La chaîne : une liste de tâches et leur ordre |
| **Tâche** | Une étape de la chaîne (une commande) |
| **Exécution** (*run*) | Un passage complet de la chaîne, lancé par l'horaire ou à la main |
| **Ordonnanceur** (*scheduler*) | Le programme qui déclenche les exécutions à l'heure et lance les tâches |

## 2. Installation légère

L'installation officielle d'Airflow dans Docker crée 7 conteneurs (Celery, Redis, plusieurs workers), prévus pour plusieurs machines. Sur un seul PC, MenuScan en utilise 3 :

| Conteneur | Rôle |
|---|---|
| `menuscan_airflow_web` | Interface web, sur http://localhost:8080 |
| `menuscan_airflow_scheduler` | Déclenche les exécutions et lance les tâches (exécuteur `LocalExecutor`) |
| `menuscan_airflow_dags` | Lit le dossier `dags/` |
| `menuscan_airflow_init` | Prépare la base au démarrage, puis s'arrête (normal) |

- **Pas de second PostgreSQL :** Airflow range ses propres données dans une base `airflow`, créée automatiquement dans le conteneur `menuscan_postgres` existant.
- **Image sur mesure** (`Dockerfile`) : Airflow 3.3.2, plus un environnement Python séparé avec dbt 1.12.7 et nos bibliothèques. Airflow et dbt ont des dépendances qui se gênent ; séparés, ils cohabitent.
- **Pas de mot de passe :** l'interface n'est ouverte qu'à ce PC (adresse 127.0.0.1). Ce réglage est réservé au poste local.

## 3. Premier démarrage, pas à pas

Depuis la racine du dépôt, Docker Desktop lancé :

1. **Construire l'image** (une seule fois, environ 5 à 10 minutes selon la connexion) :
   ```powershell
   docker compose --profile airflow build
   ```
2. **Démarrer** PostgreSQL et Airflow :
   ```powershell
   docker compose --profile airflow up -d
   ```
3. **Vérifier** que les conteneurs tournent (attendre une minute) :
   ```powershell
   docker compose --profile airflow ps
   ```
   `menuscan_postgres`, `menuscan_airflow_web`, `menuscan_airflow_scheduler` et `menuscan_airflow_dags` doivent être `Up` ou `running`. `menuscan_airflow_init` n'apparaît plus : il a fini son travail.
4. **Ouvrir** http://localhost:8080 dans le navigateur.
5. **Activer le DAG** `menuscan_chaine_complete` : un DAG est en pause à sa création. Cliquer sur l'interrupteur à côté de son nom. Airflow lance aussitôt la dernière exécution prévue (minuit) : c'est le comportement normal.
6. **Suivre** l'exécution : cliquer sur le nom du DAG. Chaque tâche passe au vert quand elle réussit. Cliquer sur une tâche puis sur *Logs* pour lire ce qu'a affiché le script (par exemple `Done. PASS=285` pour `dbt_build`).
7. **Lancer à la main** : bouton *Trigger* en haut à droite de la page du DAG.

**Durée d'une exécution :** environ 1 minute 20 sur l'environnement de test. Sur le poste de travail, `dbt_build`, la tâche la plus longue, a pris 1 min 49.

## 4. Activer, désactiver, changer l'heure

- **Activer ou mettre en pause :** l'interrupteur à droite du nom du DAG, page *Dags*. En pause, plus d'exécution automatique ; le bouton ▶ marche toujours.
- **Changer l'heure :** ligne `schedule="0 0 * * *"` de `dags/menuscan_chaine_complete.py` (minute, heure, jour du mois, mois, jour de la semaine ; `*` = tous). Exemples : `"30 21 * * *"` tous les jours à 21 h 30 ; `"0 8 * * 1"` chaque lundi à 8 h ; `None` jamais automatiquement. Airflow relit le fichier en une minute environ ; la colonne *Prochaine exécution* le confirme. Les heures sont celles de Tunis (UTC+1, sans heure d'été).
- **Démarrage avec Windows :** dans Docker Desktop, *Settings*, *General*, cocher *Start Docker Desktop when you sign in*. Les conteneurs redémarrent alors seuls (`restart: unless-stopped`), sauf s'ils ont été arrêtés avec `stop`.
- **PC éteint à l'heure prévue :** Airflow ne rattrape que la dernière exécution manquée, dès son redémarrage.

## 5. Démonstration : 36 mois livrés un par un (T5.2)

Dans une entreprise, les données arrivent chaque mois. La démonstration rejoue cette arrivée, dans une base à part, `menuscan_demo` ; l'entrepôt `menuscan_dwh` et la chaîne quotidienne ne sont pas touchés.

```
menuscan_demo_36_mois :  preparer_demo → mois_2024_01 → mois_2024_02 → … → mois_2026_12 → comparer_bases
                                              │
                                              └→ lance menuscan_mois (mois = 2024-01) et attend sa fin :
                                                 livrer_fichiers → ingerer → controler_volumes → dbt_build
```

| Élément | Rôle |
|---|---|
| `dags/menuscan_demo_36_mois.py` | Remet la démonstration à zéro, lance les 36 mois dans l'ordre, puis compare |
| `dags/menuscan_mois.py` | Traite un mois : mêmes scripts que la chaîne quotidienne, dirigés vers `menuscan_demo` (variable `MENUSCAN_DWH`) |
| `demo/livrer_mois.py` | Copie les fichiers du mois dans `menuscan_dataset/demo_arrivees`, comme une livraison |
| `demo/comparer_bases.py` | Compare 20 tables (marts et qualité) entre `menuscan_demo` et `menuscan_dwh` : nombre de lignes et empreinte MD5 du contenu ; écrit `rapport_demo.md` |

**Lancer la démonstration :** page *Dags*, bouton ▶ de `menuscan_demo_36_mois`. Durée sur un portable : probablement 30 minutes à 1 heure (estimation, environ 2,5 fois l'environnement de test). Les deux DAG de la démonstration sont actifs dès leur création : sans horaire, ils ne partent jamais seuls. Suivre les mois dans *Exécutions de Dag* (filtre `menuscan_mois`) : chaque exécution s'appelle `demo_AAAA-MM__…`.

**Règles de la démonstration :**
- **Fichiers mensuels** (commandes, lignes de commande, événements) : livrés mois par mois. **Fichiers uniques** (établissements, factures, prospects…) : livrés en entier au premier mois, car le jeu ne les découpe pas par mois (limite connue).
- **Tests dbt, mois 1 à 35 : avertissements.** À la fin d'un mois, certaines données sont encore en transit : des événements d'une session arrivent dans le fichier du mois suivant (DQ-35). Les règles qui en dépendent (DQ-11 sessions, DQ-12 session et commande, DQ-13 panier) signalent ces sessions incomplètes sans arrêter la chaîne. **Dernier mois : tests bloquants**, comme dans la chaîne quotidienne. Réglage : `--vars '{severite_tests: warn}'` (par défaut `error`, dans `05_dbt/dbt_project.yml`).
- La base `menuscan_demo` pèse environ 1 Go à la fin ; `preparer_demo` la recrée vide à chaque lancement.

**Résultat (environnement de test, 26/11/2026) :** 36 mois sur 36 réussis en 18 minutes, environ 15 secondes par mois. Avertissements : 0 aux mois 1 et 2, puis 2 à 3 règles par mois (de 7 lignes signalées en mars 2024 à 217 en novembre 2026, au rythme de la croissance de l'activité), 0 au dernier mois (285 tests sur 285). **Comparaison finale : les 20 tables sont identiques** à celles de `menuscan_dwh` (voir `rapport_demo.md`). Charger mois par mois donne exactement le même entrepôt que tout charger d'un coup.

## 6. Commandes utiles

| Commande | Effet |
|---|---|
| `docker compose up -d` | PostgreSQL seul, comme avant (application, DBeaver, dbt à la main) |
| `docker compose --profile airflow up -d` | PostgreSQL et Airflow |
| `docker compose --profile airflow stop` | Arrête tout, sans rien effacer |
| `docker compose --profile airflow logs airflow-scheduler --tail 50` | 50 dernières lignes du journal de l'ordonnanceur |
| `docker stats --no-stream` | Mémoire et processeur utilisés par chaque conteneur |

Les journaux des tâches sont aussi écrits dans `06_orchestration/logs/` (exclu de Git).

## 7. Si quelque chose ne marche pas

| Symptôme | Cause probable | Solution |
|---|---|---|
| La page http://localhost:8080 ne s'ouvre pas | Airflow démarre encore | Attendre une minute, puis recharger |
| Le DAG n'apparaît pas | Le lecteur de DAG n'a pas encore lu le dossier | Attendre 30 secondes, recharger |
| `menuscan_airflow_init` en erreur | PostgreSQL inaccessible ou mot de passe | `docker compose --profile airflow logs airflow-init` et m'envoyer la fin |
| PC très lent | Docker manque de mémoire | `docker stats --no-stream` ; arrêter Airflow quand il ne sert pas |
| Tâche `dbt_build` rouge | Un test dbt échoue | Ouvrir les *Logs* de la tâche, chercher `FAIL` |

## 8. Vérifié (26/11/2026)

### Environnement de test

Docker n'est pas disponible sur l'environnement de test : la même architecture y a été reproduite avec 3 processus (interface web, ordonnanceur, lecteur de DAG), l'exécuteur `LocalExecutor` et une base `airflow` dans PostgreSQL, avec les mêmes réglages que `docker-compose.yml`.

| Vérification | Résultat |
|---|---|
| Santé des composants (API `/api/v2/monitor/health`) | base, ordonnanceur et lecteur de DAG : `healthy` |
| Exécution planifiée (6 h) et exécution manuelle | 5 tâches sur 5 réussies, chacune ; la seconde a attendu la fin de la première (`max_active_runs=1`) |
| Durée d'une exécution | 1 min 18 (dont `dbt_build` 40 s et `controler_entrepot` 29 s) |
| Dossier de données absent | `verifier_sources` échoue, les tâches suivantes ne sont pas lancées |
| Mémoire des 3 processus Airflow | environ 0,5 Go (hors Docker ; à mesurer sur le poste avec `docker stats`) |

### Poste de travail (Windows 10, 16 Go de RAM, Docker Desktop)

| Vérification | Résultat |
|---|---|
| Démarrage | 4 conteneurs `Up` ; `menuscan_airflow_init` terminé (`Exited`) après création de la base `airflow` |
| Exécution de 6 h (déclenchée à l'activation) et exécution manuelle | 5 tâches sur 5 réussies, chacune ; `dbt_build` : `Done. PASS=285 WARN=0 ERROR=0` |
| Mémoire (`docker stats`, pendant `dbt_build`) | Airflow : 1,0 Go pour les 3 conteneurs ; PostgreSQL : 1,35 Go ; limite de Docker : 5,8 Go |

### Démonstration mois par mois sur le poste de travail

| Vérification | Résultat |
|---|---|
| `menuscan_demo_36_mois` | 38 tâches sur 38 réussies, en 44 min 21 (45 s par mois au début, 3 min 15 au dernier mois : le volume grandit avec l'activité) |
| `menuscan_mois` | 36 exécutions réussies, dans l'ordre des mois ; dernier mois : `dbt_build` en 2 min 45, tests bloquants |
| Comparaison finale | 20 tables sur 20 identiques à `menuscan_dwh` (`rapport_demo.md`) |

**Erreurs corrigées :** l'heure des rapports écrits par les conteneurs était en UTC (ajout de `TZ: Africa/Tunis`).

**Erreur corrigée au premier démarrage :** l'adresse de la base produite par `config/url_base.py` finissait par un saut de ligne, qu'Airflow gardait dans le nom de la base (`airflow\n`, introuvable) ; corrigé par `print(..., end="")`, vérifié avant et après sur l'environnement de test.
