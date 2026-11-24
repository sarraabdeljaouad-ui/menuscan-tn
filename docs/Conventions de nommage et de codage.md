# Conventions de nommage et de codage

**Référence :** MS-DATA-CNV-001 · **Version :** 1.0 · **Date :** 23/11/2026 · **Auteure :** Sarra Abdeljaouad

Ces règles s'appliquent à tout le projet. Elles reprennent les conventions du jeu de données et du référentiel des données (MS-DATA-REF-001).

## 1. Règles générales

- **Langue :** noms de tables, de colonnes, de modèles, de mesures et documents en français, sans accent dans les noms techniques.
- **Casse :** `snake_case` en minuscules pour tout nom technique (tables, colonnes, fichiers Python, modèles dbt).
- **Clarté :** un nom dit ce que contient l'objet, sans abréviation obscure : `montant_total_ttc` et pas `mt_tot`.
- **Unités dans le nom** quand elles ne sont pas évidentes : `_ht`, `_ttc`, `_heures`, `_pct`.

## 2. Données

| Élément | Règle | Exemple |
|---|---|---|
| Table | Nom au pluriel pour les tables de données, préfixe pour les référentiels | `commandes`, `ref_villes`, `dim_calendrier` |
| Clé primaire | `<entité>_id` | `etablissement_id` |
| Clé étrangère | Même nom que la clé référencée ; préfixe de rôle si plusieurs | `formule_initiale_id`, `parrain_etablissement_id` |
| Identifiant | Préfixe de 3 lettres + numéro à largeur fixe | `ETB0001`, `CMD0000001` |
| Date | `date_<événement>` | `date_signature` |
| Horodatage | `date_heure_<événement>` ou nom explicite | `date_heure_commande`, `debut_session` |
| Booléen | `est_<état>` ou `a_<action>` | `est_ramadan`, `a_commande` |
| Montant | 3 décimales, en dinars, HT ou TTC dans le nom | `prix_mensuel_ht` |
| Statut | Valeur en minuscules, sans accent | `servie`, `payee_en_retard` |

Formats : dates `AAAA-MM-JJ`, horodatages `AAAA-MM-JJ HH:MM:SS` en heure de Tunis (UTC+1), CSV en UTF-8 avec virgule comme séparateur et point décimal.

## 3. Bases de données

| Élément | Règle |
|---|---|
| Bases | `menuscan_app` (application), `menuscan_dwh` (entrepôt) |
| Schémas de l'entrepôt | `raw` (brut), `staging`, `intermediate`, `marts`, `ml`, `quarantaine` |
| Tables brutes | Même nom que la table du référentiel : `raw.commandes` |
| Colonnes techniques | `_fichier_source`, `_date_chargement` (préfixe `_`) |
| Requêtes SQL | Mots-clés en majuscules, une clause par ligne, alias explicites |

## 4. dbt

| Couche | Préfixe | Matérialisation | Exemple |
|---|---|---|---|
| Staging | `stg_` | Vue | `stg_commandes` |
| Intermediate | `int_` | Table | `int_sessions`, `int_abonnement_mensuel` |
| Marts : faits | `fait_` | Table (incrémentale si volume) | `fait_ligne_commande` |
| Marts : dimensions | `dim_` | Table | `dim_etablissement` |
| Seeds | `seed_` | Table | `seed_correspondance_statuts` |
| Snapshots | `snap_` | Snapshot | `snap_etablissements` |

- Un modèle `stg_` lit une seule source et ne fait que renommer, typer, normaliser et dédoublonner.
- Chaque modèle a une description et des tests dans un fichier `.yml` du même dossier.
- Un test spécifique porte le code de sa règle : `tests/dq_03_montant_commande.sql`.

## 5. Python

- Style PEP 8, formatage automatique avec `black`, lignes de 120 caractères au plus.
- Fichiers et fonctions en `snake_case` ; constantes en MAJUSCULES.
- Chemins par `pathlib` et variables d'environnement, jamais de chemin écrit en dur ni de mot de passe dans le code.
- Notebooks numérotés (`01_eda.ipynb`) ; sorties conservées pour la lecture, mais chaque notebook doit pouvoir se relancer de bout en bout.

## 6. Power BI

| Élément | Règle | Exemple |
|---|---|---|
| Mesure | Nom métier en français, code KPI en description | `MRR`, `Taux de résiliation` |
| Mesure de comparaison | Suffixe explicite | `MRR A-1`, `MRR évolution %` |
| Table de mesures | Une table `_Mesures` | – |
| Page | Code et nom du tableau de bord | `TB-1 Croissance` |

## 7. Git

- **Branche principale :** `main`, toujours fonctionnelle.
- **Branches de travail :** `phase-<n>-<sujet>`, par exemple `phase-4-staging`.
- **Messages de commit :** en français, au présent, préfixés par le type : `ajout:`, `correction:`, `doc:`, `refonte:`, `test:`. Exemple : `ajout: modèle stg_commandes avec dédoublonnage`.
- **Fusion :** dans `main` seulement si les tests dbt passent.

## 8. Documents

- **Code :** `MS-DATA-<TYPE>-<NNN>`, par exemple `MS-DATA-NCA-001` pour la note de cadrage.
- **Version :** 1.0 à la première validation ; 1.1, 1.2 pour les corrections ; 2.0 pour un changement de fond.
- **Nom de fichier :** numéro d'ordre dans le dossier, puis titre : `2-Note de cadrage du projet.docx`.
- **Date :** jour de rédaction ou de mise à jour (décision D-07).

## 9. Règles de qualité et registres

- Règles de qualité : `DQ-01` à `DQ-38`, définies dans le catalogue (MS-DATA-DQV-002).
- Registres : décisions `D-xx`, actions `A-xx`, points ouverts `PO-xx`, risques `Rxx`, jalons `Jx`.
- Besoins `BM-xx`, exigences `EF-xx` et `ENF-xx`, règles de gestion `RG-xx`, indicateurs `Kxx`.
