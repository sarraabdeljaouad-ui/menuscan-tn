# 05_dbt : entrepôt de données (phase 4)

**Auteure :** Sarra Abdeljaouad · **Date :** 25/11/2026 · **Tâche :** T4.1 (staging et quarantaine) · **Outil :** dbt Core 1.12 (décisions D-20 et D-31)

Ce dossier transforme la couche brute (`raw`, phase 3) en données propres. T4.1 livre le premier étage : le **staging**, qui nettoie chaque table, et la **quarantaine**, qui garde les lignes écartées.

## 1. Prise en main de dbt

Ce guide remplace le tutoriel officiel (action A-07). Il suffit de le lire une fois, en lançant les commandes au fur et à mesure.

### dbt en une phrase

dbt exécute des fichiers `SELECT` dans le bon ordre et range chaque résultat dans une table ou une vue de PostgreSQL. On écrit seulement le `SELECT` ; dbt écrit le `CREATE TABLE`, gère l'ordre des modèles et teste le résultat.

### Vocabulaire

| Mot | Sens | Exemple dans le projet |
|---|---|---|
| **Source** | Table déjà présente dans la base, que dbt lit sans la créer | `raw.ventes_commandes`, déclarée dans `models/staging/_sources.yml` |
| **Modèle** | Un fichier `.sql` qui contient un `SELECT` ; dbt en fait une table ou une vue du même nom | `models/staging/stg_commandes.sql` devient la vue `staging.stg_commandes` |
| **`ref()`** | Lien vers un autre modèle. dbt en déduit l'ordre de construction | `from {{ ref('prep_commandes') }}` |
| **`source()`** | Lien vers une source | `from {{ source('raw', 'ventes_commandes') }}` |
| **Matérialisation** | Forme du résultat : `table` (données copiées) ou `view` (requête enregistrée) | Préparation en tables, staging en vues |
| **Macro** | Morceau de SQL réutilisable, écrit en Jinja (`{{ }}`, `{% %}`) | `{{ telephone('telephone') }}` met un numéro au format +216 |
| **Seed** | Petit fichier CSV que dbt charge comme une table | `seeds/correspondance_libelles.csv` (served -> servie) |
| **Test** | Requête qui cherche des erreurs ; le test passe si elle ne renvoie rien | Identifiant unique, clé étrangère existante, valeur autorisée |

### Lancer dbt

Toutes les commandes se lancent **depuis la racine du dépôt**, environnement Python activé, Docker lancé. Le script `lancer_dbt.py` lit le mot de passe dans `.env`, puis passe la commande à dbt :

```powershell
python 05_dbt/lancer_dbt.py debug
```

| Commande (après `python 05_dbt/lancer_dbt.py`) | Ce qu'elle fait |
|---|---|
| `debug` | Vérifie la connexion à `menuscan_dwh`. À lancer en premier : la dernière ligne doit dire « All checks passed! » |
| `seed` | Charge les fichiers CSV de `seeds/` |
| `run` | Construit tous les modèles, dans l'ordre |
| `test` | Lance tous les tests |
| `build` | Fait tout : seed, run et test, dans le bon ordre. **C'est la commande habituelle** |
| `build --select stg_commandes` | Ne construit et ne teste qu'un modèle |
| `build --select prep_commandes+` | Un modèle et tout ce qui en dépend (le `+` après le nom) |
| `docs generate` puis `docs serve` | Construit puis ouvre dans le navigateur la documentation du projet, avec le graphe de lignage. `Ctrl+C` pour arrêter |

Un `build` complet prend environ 20 secondes sur l'environnement de test (plus sur un portable). La dernière ligne doit être `Done. PASS=133 WARN=0 ERROR=0`.

**Si un test échoue**, dbt affiche `FAIL` et le nom du test. Pour voir la requête et les lignes fautives : `python 05_dbt/lancer_dbt.py test --select <nom_du_modèle> --store-failures`. Les lignes en erreur sont alors enregistrées dans le schéma `dbt_test__audit`.

### Premier lancement, pas à pas

1. `python 05_dbt/lancer_dbt.py debug` : vérifier la connexion.
2. `python 05_dbt/lancer_dbt.py build` : construire et tester.
3. Dans DBeaver, rafraîchir `menuscan_dwh` : trois nouveaux schémas apparaissent, `preparation`, `staging` et `qualite`, plus `referentiels` pour le seed.
4. Lancer la requête du bilan (§ 4) pour voir ce que le nettoyage a fait.

## 2. Organisation

```
raw (phase 3)  →  preparation.prep_*  →  staging.stg_*        (lignes valides)
                                     ↘  qualite.quarantaine   (lignes écartées, avec la règle)
                                     ↘  qualite.corrections   (valeurs corrigées, avant et après)
```

| Dossier | Schéma | Contenu |
|---|---|---|
| `models/staging/preparation/` | `preparation` | Un modèle `prep_<table>` par source : **toutes** les lignes brutes, typées et nettoyées, avec trois colonnes de contrôle : `_corrections`, `_regle_rejet`, `_motif_rejet` |
| `models/staging/` | `staging` | Un modèle `stg_<table>` par source : les lignes de la préparation que rien n'a rejetées. Noms des modèles repris du dossier de modélisation (phase 0) |
| `models/qualite/` | `qualite` | `quarantaine`, `corrections` et `bilan_qualite` |
| `seeds/` | `referentiels` | Table de correspondance des libellés (anglais, synonymes, casse) |
| `macros/` | | Fonctions de nettoyage (`nettoyage.sql`), règles de rejet (`rejet.sql`), noms de référence, staging |
| `tests/` | | Deux tests propres au projet : aucune ligne perdue entre raw, staging et quarantaine |

**Règle du projet : une ligne n'est jamais perdue.** Chaque ligne brute est soit en staging, soit en quarantaine, avec sa règle et son motif. Les tests `aucune_ligne_perdue` et `preparation_complete` le vérifient à chaque `build`.

## 3. Règles traitées en T4.1

Règles du catalogue qualité (`00_cadrage/4-Gouvernance des données/2-Catalogue Regles Qualite.xlsx`) dont l'étape est « Staging » :

| Règle | Traitement | Tables |
|---|---|---|
| DQ-01 | Identifiant vide : quarantaine | toutes |
| DQ-02 | Article ou commande inconnus : quarantaine | lignes_commande, evenements, paiements |
| DQ-04 | Montant de ligne recalculé = prix × quantité | lignes_commande |
| DQ-05 | Quantité nulle ou négative : quarantaine | lignes_commande, evenements |
| DQ-15 | TTC recalculé quand il ne vaut pas net HT + TVA | factures |
| DQ-18 | Second paiement réussi, montant différent du TTC, paiement réussi avant l'émission : quarantaine | paiements |
| DQ-23 | Dépense négative, clics supérieurs aux impressions, jour hors campagne : quarantaine | marketing_depenses_quotidiennes |
| DQ-27 | Date après le 31/12/2026, événement pendant la panne du 12/09/2025 : quarantaine | commandes, evenements, paiements, tickets |
| DQ-28 | Date « JJ/MM/AAAA HH:MI » convertie (les secondes manquent dans la source) | commandes |
| DQ-29 | Doublon d'ingestion : la première copie reçue est gardée, les autres vont en quarantaine | toutes |
| DQ-31 | Téléphone au format +216 et 8 chiffres ; e-mail réparé (espaces, @ manquant) | etablissements, prospects |
| DQ-32 | Libellés normalisés : codes par la table de correspondance, noms par leur écriture la plus fréquente | abonnements, articles, commandes, etablissements, evenements, paiements, prospects, tickets |
| DQ-33 | Montant de 1 000 DT ou plus divisé par 1 000 (millimes) | articles, articles_prix_historique, lignes_commande, paiements |
| DQ-34 | Heure UTC convertie en heure de Tunis | evenements, paiements |
| DQ-35 | Donnée en retard : rattachée à sa date, pas au mois du fichier ; le retard est tracé | commandes, evenements |
| DQ-36 | Format français (virgule décimale, JJ/MM/AAAA) converti | factures, marketing_depenses_quotidiennes |
| DQ-38 | Champ obligatoire vide : nombre de tables recompté, catégorie et mode de règlement mis à « non renseigné » | etablissements, tickets_support, commandes |

**Choix à connaître :**
- **Noms de plats et d'établissements (DQ-32) :** la forme de référence est l'écriture la plus fréquente du même nom (même clé sans casse, sans accent, espaces normalisés), en écartant les écritures tout en majuscules ou tout en minuscules. Aucune donnée extérieure n'est utilisée.
- **Millimes (DQ-33) :** le seuil de 1 000 DT est une variable (`seuil_millimes` dans `dbt_project.yml`). Aucun prix ni paiement légitime du jeu n'atteint 1 000 DT.
- **Retards (DQ-35) :** les journaux de tracking sont découpés par mois en heure UTC ; le retard d'un événement se mesure donc en UTC.

**Laissé à T4.2 (étage intermediate, selon le catalogue) :** total de commande recalculé depuis les lignes (DQ-03), fusion des 6 doublons d'établissement (DQ-30), horloges d'appareil décalées (DQ-37), reconstitution des sessions.

## 4. Résultats vérifiés (25/11/2026, environnement de test)

```sql
-- bilan par table et par règle
SELECT * FROM qualite.bilan_qualite WHERE nb_lignes > 0;
```

| Élément | Valeur |
|---|---|
| Lignes brutes | 2 015 451 |
| Lignes en staging | 1 997 548 |
| Lignes en quarantaine | 17 903 : 17 265 doublons (DQ-29), 383 identifiants inconnus (DQ-02), 240 quantités non positives (DQ-05), 15 dépenses (DQ-23) |
| Valeurs corrigées | 12 266 |
| Tests dbt | 133 éléments, 0 erreur (89 tests : 19 unicités, 25 valeurs obligatoires, 30 clés étrangères, 13 listes de valeurs, 2 tests propres au projet) |

**Comparaison avec la couche de référence** (faite hors de dbt, avec le corrigé non publié) : le staging est identique à la référence, valeur par valeur, sauf sur ces points :
- ce qui relève de T4.2 (6 doublons d'établissement, 213 totaux de commande, 1 322 horloges décalées) ;
- ce que la source ne permet pas de retrouver (secondes des 1 067 dates au format français, 517 modes de règlement et 10 catégories vides) ;
- les 15 dépenses en quarantaine et les 11 commandes en retard non livrées (décision D-32).

95,1 % des 31 718 anomalies injectées sont déjà retrouvées. La mesure officielle, demandée pour le jalon J5, sera faite en T4.4.

## 5. Fichiers

| Fichier | Rôle |
|---|---|
| `dbt_project.yml` | Configuration du projet : schémas, matérialisations, variables (date d'arrêté, panne, seuil des millimes, fuseau) |
| `profiles.yml` | Connexion à `menuscan_dwh` ; le mot de passe vient de `.env` |
| `lancer_dbt.py` | Lance dbt avec les variables de `.env` |
| `.gitignore` | Exclut `target/` et `logs/` (fichiers générés par dbt) |
