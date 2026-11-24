# Installation du poste de travail

**Référence :** MS-DATA-INS-001 · **Version :** 1.1 · **Date :** 23/11/2026 · **Auteure :** Sarra Abdeljaouad

Ce guide prépare un poste Windows pour tout le projet. Les outils sont gratuits. PostgreSQL tourne dans Docker (décision D-17).

## 1. Outils à installer

| Outil | Usage | Phase |
|---|---|---|
| Git | Versionnement du code | 0 |
| Python 3.11 | Générateur, ingestion, application, ML | 0 |
| VS Code | Édition du code et des notebooks | 0 |
| Docker Desktop | PostgreSQL, puis Airflow | 1 |
| DBeaver Community | Exploration des bases | 1 |
| Power BI Desktop | Tableaux de bord | 6 |
| draw.io (application ou site) | Modèles de données | 0 |

Installer chaque outil depuis son site officiel. Docker Desktop sous Windows demande WSL 2 : suivre l'assistant d'installation de Docker.

## 2. Récupérer le projet

```bash
git clone https://github.com/sarraabdeljaouad-ui/menuscan-tn.git
cd menuscan-tn
```

Pour travailler sur le jeu complet, télécharger le ZIP depuis la page Releases du dépôt et le décompresser à côté du dépôt (dossier `menuscan_dataset/`, exclu de Git).

## 3. Environnement Python

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Contenu prévu de `requirements.txt` (versions à figer au démarrage de la phase 1, avec `pip freeze`) :

```
pandas
numpy
pyarrow
sqlalchemy
psycopg2-binary
dbt-postgres
streamlit
qrcode[pil]
scikit-learn
statsmodels
mlxtend
mlflow
matplotlib
jupyter
black
```

Vérification :

```bash
python -c "import pandas, sqlalchemy, streamlit, sklearn; print('ok')"
dbt --version
```

## 4. PostgreSQL dans Docker

Créer le fichier `.env` à partir de `.env.example` :

```
POSTGRES_USER=menuscan
POSTGRES_PASSWORD=choisir_un_mot_de_passe
POSTGRES_PORT=5432
```

Fichier `docker-compose.yml` (version de la phase 1) :

```yaml
services:
  postgres:
    image: postgres:16
    container_name: menuscan_postgres
    env_file: .env
    environment:
      POSTGRES_DB: menuscan_app
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./02_oltp/init:/docker-entrypoint-initdb.d
volumes:
  pgdata:
```

Script `02_oltp/init/01_bases.sql`, exécuté au premier démarrage :

```sql
CREATE DATABASE menuscan_dwh;
```

Démarrer et vérifier :

```bash
docker compose up -d
docker ps                                   # le conteneur menuscan_postgres doit être « Up »
docker exec -it menuscan_postgres psql -U menuscan -d menuscan_app -c "SELECT version();"
```

Connexion depuis DBeaver : hôte `localhost`, port `5432`, utilisateur et mot de passe du fichier `.env`, bases `menuscan_app` et `menuscan_dwh`.

## 5. Charger la base applicative (phase 1)

```bash
docker cp menuscan_dataset/sql/schema_postgres.sql menuscan_postgres:/tmp/
docker exec -it menuscan_postgres psql -U menuscan -d menuscan_app -f /tmp/schema_postgres.sql
```

Les données se chargent ensuite table par table, dans l'ordre indiqué à la fin du fichier `schema_postgres.sql`, avec le script Python de la phase 1. Les contrôles de `sql/controles_qualite.sql` doivent tous renvoyer 0.

## 6. dbt

Fichier `%USERPROFILE%\.dbt\profiles.yml` :

```yaml
menuscan:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: menuscan
      password: "{{ env_var('POSTGRES_PASSWORD') }}"
      dbname: menuscan_dwh
      schema: staging
      threads: 4
```

Vérification, depuis le dossier `05_dbt/` :

```bash
dbt debug
```

## 7. Power BI Desktop

Connexion : Obtenir les données → Base de données PostgreSQL → serveur `localhost:5432`, base `menuscan_dwh`. Mode Import. Si la connexion échoue, consulter la documentation Microsoft du connecteur PostgreSQL pour le pilote requis par ta version.

## 8. Vérification finale

Le script `outils/verifier_poste.py` fait ces contrôles en une fois, depuis la racine du dépôt, environnement Python activé :

```bash
python outils/verifier_poste.py
```

Il affiche un tableau OK / KO et se termine par le nombre de contrôles réussis. Les contrôles détaillés sont repris ci-dessous.


| Contrôle | Commande ou action | Résultat attendu |
|---|---|---|
| Python | `python --version` | Python 3.11 |
| Bibliothèques | `python -c "import pandas, streamlit"` | Aucune erreur |
| Docker | `docker ps` | `menuscan_postgres` en état « Up » |
| Bases | DBeaver | `menuscan_app` et `menuscan_dwh` visibles |
| dbt | `dbt debug` | « All checks passed! » |
| Git | `git status` | Aucun fichier de données ni `.env` à valider |

## 9. Problèmes fréquents

| Problème | Cause probable | Solution |
|---|---|---|
| Le port 5432 est déjà utilisé | Un PostgreSQL Windows tourne déjà | Changer `POSTGRES_PORT` dans `.env` (par exemple 5433) |
| `docker compose` introuvable | Docker Desktop arrêté | Lancer Docker Desktop, attendre qu'il soit prêt |
| La base `menuscan_dwh` n'existe pas | Le volume existait avant le script d'initialisation | `docker compose down -v` puis `docker compose up -d` (efface les données) |
| `dbt debug` échoue sur le mot de passe | Variable non définie dans la session | Définir `POSTGRES_PASSWORD` dans la session ou dans les variables d'environnement Windows |
