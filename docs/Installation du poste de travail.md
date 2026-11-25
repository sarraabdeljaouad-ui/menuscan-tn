# Installation du poste de travail

**Référence :** MS-DATA-INS-001 · **Version :** 1.4 · **Date :** 25/11/2026 · **Auteure :** Sarra Abdeljaouad

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

Le conteneur publie PostgreSQL sur le port **5440** du poste, et non sur 5432 : le port 5432 est souvent pris par un PostgreSQL installé sous Windows (décision D-19). À l'intérieur du conteneur, PostgreSQL reste sur 5432.

Créer le fichier `.env` à partir de `.env.example` :

```
POSTGRES_USER=menuscan
POSTGRES_PASSWORD=choisir_un_mot_de_passe
POSTGRES_PORT=5440
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

Connexion depuis DBeaver : hôte `localhost`, port `5440`, utilisateur et mot de passe du fichier `.env`, bases `menuscan_app` et `menuscan_dwh`.

## 5. Charger la base applicative (phase 1)

1. Télécharger `menuscan_dataset_v1.0.zip` depuis la page Releases du dépôt.
2. Le décompresser **à la racine du dépôt** : on doit obtenir `menuscan-tn/menuscan_dataset/donnees_reference/`. Si Windows crée un dossier intermédiaire (`menuscan_dataset_v1.0/menuscan_dataset/`), déplacer `menuscan_dataset` d'un niveau. Le dossier est exclu de Git.
3. Lancer le chargement, conteneur démarré et environnement Python activé :

```bash
python 02_oltp/charger_base_app.py
```

Le script crée les 20 tables du schéma `menuscan` dans `menuscan_app`, les charge avec `COPY`, compare le nombre de lignes à celui des fichiers, puis exécute les 23 contrôles de `02_oltp/controles_qualite.sql` (0 violation attendue). Il écrit le résultat dans `02_oltp/rapport_chargement.md`. Durée constatée : environ 30 secondes.

Pour tout recharger : `python 02_oltp/charger_base_app.py --reinitialiser`.

Le chargement applique ensuite les migrations de `02_oltp/migrations/` (évolutions du modèle pour l'application). Sur une base chargée avant une migration, l'appliquer seule : `python 02_oltp/charger_base_app.py --migrer`. Pour relancer seulement les 23 contrôles qualité : `python 02_oltp/charger_base_app.py --controles`.

## 6. dbt

Fichier `%USERPROFILE%\.dbt\profiles.yml` :

```yaml
menuscan:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5440
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

Connexion : Obtenir les données → Base de données PostgreSQL → serveur `localhost:5440`, base `menuscan_dwh`. Mode Import. Si la connexion échoue, consulter la documentation Microsoft du connecteur PostgreSQL pour le pilote requis par ta version.

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
| Le port 5440 est déjà utilisé | Un autre service écoute sur ce port | Choisir un port libre (`netstat -ano \| findstr :5441` ne doit rien renvoyer) et le mettre dans `POSTGRES_PORT` |
| `docker compose` introuvable | Docker Desktop arrêté | Lancer Docker Desktop, attendre qu'il soit prêt |
| La base `menuscan_dwh` n'existe pas | Le volume existait avant le script d'initialisation | `docker compose down -v` puis `docker compose up -d` (efface les données) |
| `dbt debug` échoue sur le mot de passe | Variable non définie dans la session | Définir `POSTGRES_PASSWORD` dans la session ou dans les variables d'environnement Windows |
| `docker ps` répond « 500 Internal Server Error » ; l'application reste sur « Connexion à la base de données… » ou affiche « La base de données ne répond pas » | Moteur Docker bloqué après un redémarrage du PC (Docker Desktop affiche « Engine running » sans chiffres de RAM ni de CPU) | Quitter Docker Desktop (clic droit sur la baleine, Quit), lancer `wsl --shutdown`, rouvrir Docker Desktop, puis `docker compose up -d` et `python outils/verifier_poste.py`. Ne jamais utiliser « Clean / Purge data » ni « Reset to factory defaults » : ils effacent la base |
| Les QR codes ou le téléphone n'ouvrent plus le menu | L'adresse du PC sur le Wi-Fi a changé (elle s'affiche en « Network URL » au lancement de Streamlit) | Mettre la nouvelle adresse dans `CLIENT_URL` du fichier `.env`, relancer l'application équipe et réimprimer les QR codes |

## 10. Changer le mot de passe de PostgreSQL

Le mot de passe de `.env` n'a servi qu'à la création de la base. Changer seulement `.env` coupe toutes les connexions : il faut d'abord changer le mot de passe dans PostgreSQL, puis écrire le même dans `.env`. Choisir des lettres, des chiffres, `-` et `_` (pas d'espace, ni `$`, `#` ou guillemets, que Docker Compose interprète).

1. `docker exec -it menuscan_postgres psql -U menuscan -d menuscan_app` : l'invite devient `menuscan_app=#`.
2. `\password menuscan` : taper le nouveau mot de passe deux fois (rien ne s'affiche, c'est normal), puis `\q`.
3. `notepad .env` : remplacer la valeur de `POSTGRES_PASSWORD=` (sans guillemets), enregistrer.
4. `python outils/verifier_poste.py` : 11 contrôles réussis sur 11. « password authentication failed » signifie que les deux mots de passe diffèrent.
5. Relancer les deux applications, puis mettre à jour le mot de passe de la connexion DBeaver (clic droit, Edit Connection).
