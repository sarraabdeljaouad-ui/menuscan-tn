# 05_dbt : entrepôt de données (phase 4)

**Auteure :** Sarra Abdeljaouad · **Date :** 25/11/2026 · **Tâches :** T4.1 (staging et quarantaine), T4.2 (intermediate), T4.3 (marts et snapshot), T4.4 (tests DQ et validation) · **Outil :** dbt Core 1.12 (décisions D-20 et D-31)

Ce dossier transforme la couche brute (`raw`, phase 3) en données propres. T4.1 livre le **staging**, qui nettoie chaque table, et la **quarantaine**, qui garde les lignes écartées. T4.2 livre l'étage **intermediate** : sessions reconstituées, totaux de commande recalculés, établissements dédoublonnés, horloges corrigées et MRR mensuel. T4.3 livre les **marts** : le modèle en étoile que lira Power BI, et un **snapshot** qui historise les établissements.

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
| **Snapshot** | Copie historisée d'une table : dbt ferme l'ancienne version d'une ligne quand elle change et en ouvre une nouvelle (SCD2) | `snapshots/snp_etablissements.yml` |

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
| `snapshot` | Met à jour les snapshots seulement (historique des établissements) |
| `build` | Fait tout : seed, run, snapshot et test, dans le bon ordre. **C'est la commande habituelle** |
| `build --select stg_commandes` | Ne construit et ne teste qu'un modèle |
| `build --select prep_commandes+` | Un modèle et tout ce qui en dépend (le `+` après le nom) |
| `docs generate` puis `docs serve` | Construit puis ouvre dans le navigateur la documentation du projet, avec le graphe de lignage. `Ctrl+C` pour arrêter |
| `test --select "path:tests/dq"` | Lance seulement les 27 tests des règles DQ-01 à DQ-27 |

Un `build` complet prend environ 30 secondes sur l'environnement de test (plus sur un portable). La dernière ligne doit être `Done. PASS=285 WARN=0 ERROR=0`.

**Si un test échoue**, dbt affiche `FAIL` et le nom du test. Pour voir la requête et les lignes fautives : `python 05_dbt/lancer_dbt.py test --select <nom_du_modèle> --store-failures`. Les lignes en erreur sont alors enregistrées dans le schéma `dbt_test__audit`.

### Premier lancement, pas à pas

1. `python 05_dbt/lancer_dbt.py debug` : vérifier la connexion.
2. `python 05_dbt/lancer_dbt.py build` : construire et tester.
3. Dans DBeaver, ouvrir un éditeur SQL **sur `menuscan_dwh`** (clic droit sur la base, `SQL Editor`, `New SQL script`) et rafraîchir (F5) : les schémas `preparation`, `staging`, `intermediate`, `marts`, `snapshots`, `qualite` et `referentiels` apparaissent.
4. Lancer la requête du bilan (§ 4) pour voir ce que le nettoyage a fait.

## 2. Organisation

```
raw (phase 3)  →  preparation.prep_*  →  staging.stg_*  →  intermediate.int_*  →  marts.fait_* et marts.dim_*  (Power BI)
                                                                            ↘  snapshots.snp_etablissements
                                     ↘  qualite.quarantaine   (lignes écartées, avec la règle)
                                     ↘  qualite.corrections   (valeurs corrigées, avant et après, staging et intermediate)
```

| Dossier | Schéma | Contenu |
|---|---|---|
| `models/staging/preparation/` | `preparation` | Un modèle `prep_<table>` par source : **toutes** les lignes brutes, typées et nettoyées, avec trois colonnes de contrôle : `_corrections`, `_regle_rejet`, `_motif_rejet` |
| `models/staging/` | `staging` | Un modèle `stg_<table>` par source : les lignes de la préparation que rien n'a rejetées. Noms des modèles repris du dossier de modélisation (phase 0) |
| `models/intermediate/` | `intermediate` | Modèles `int_*` : règles qui croisent plusieurs lignes ou plusieurs tables (§ 4) |
| `models/marts/` | `marts` | Modèle en étoile : 8 faits, 9 dimensions (§ 5) |
| `snapshots/` | `snapshots` | Snapshot SCD2 des établissements (§ 5) |
| `models/qualite/` | `qualite` | `quarantaine`, `corrections` et `bilan_qualite` |
| `seeds/` | `referentiels` | Table de correspondance des libellés (anglais, synonymes, casse) |
| `macros/` | | Fonctions de nettoyage (`nettoyage.sql`), règles de rejet (`rejet.sql`), noms de référence, staging |
| `tests/` | | Tests propres au projet : aucune ligne perdue, cohérence des sessions, pont du MRR, totaux des marts |
| `tests/dq/` | | Un test par règle DQ-01 à DQ-27 (§ 6) |
| `controler_entrepot.py` | | Mesure des anomalies retrouvées et comparaison avec la référence ; écrit `rapport_validation.md` |

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

## 4. Étage intermediate (T4.2)

| Modèle | Contenu | Règle |
|---|---|---|
| `int_horodatages_corriges` | Événements dont l'horloge du téléphone a reculé, avec l'heure corrigée | DQ-37 |
| `int_evenements` | Événements valides avec l'heure corrigée (vue) | DQ-37 |
| `int_sessions` | 296 166 sessions reconstituées : début, fin, appareil, langue, articles vus, panier, commande, nombre d'événements | DQ-11 |
| `int_commandes` | Total, nombre de lignes et nombre d'articles recalculés depuis les lignes | DQ-03 |
| `int_correspondance_etablissements` | Table de correspondance ancien identifiant → identifiant gardé, avec le motif | DQ-30 |
| `int_etablissements` | 403 établissements, sans les 6 identifiants fusionnés | DQ-30 |
| `int_mrr_mensuel` | Un établissement × un mois : MRR, MRR du mois précédent, variation, mouvement | |
| `int_corrections` | Corrections de cet étage, reprises dans `qualite.corrections` | |

**Choix à connaître :**
- **Horloges décalées (DQ-37) :** dans une session, les identifiants d'événements suivent l'ordre d'émission. Un événement horodaté avant un événement émis plus tôt est « hors rang ». Il est avancé du plus petit nombre de minutes entières qui le replace entre ses voisins. Un décalage qui laisse l'événement dans l'ordre est indétectable.
- **Sessions :** les événements écartés pour article inconnu (DQ-02) comptent dans la session, car la consultation a bien eu lieu ; les doublons (DQ-29) ne comptent pas.
- **Totaux de commande (DQ-03) :** ils sont recalculés seulement si toutes les lignes de la commande sont en staging. Si une ligne est en quarantaine, les valeurs de la source sont gardées et `lignes_completes` vaut faux (359 commandes).
- **Doublons d'établissement (DQ-30) :** même nom normalisé et même téléphone. L'identifiant gardé est celui qui porte le plus d'abonnements, puis le plus petit.
- **MRR (décision D-33) :** prix mensuel HT catalogue de l'abonnement actif le dernier jour du mois, abonnés annuels compris (sans la remise de 2 mois), mois de mise en service compris. Deux montées de gamme datées du 01/01/2027 sont hors période.


## 5. Marts et snapshot (T4.3)

Le modèle en étoile reprend celui du dossier de modélisation (phase 0). Les clés des dimensions sont les identifiants métier (`etablissement_id`, `prix_id`...) ; la clé de date est un entier `AAAAMMJJ` (`date_id`).

| Fait | Grain | Lignes | KPI servis |
|---|---|---:|---|
| `fait_ligne_commande` | Un article commandé | 239 353 | Chiffre d'affaires des établissements, articles vendus |
| `fait_commande` | Une commande | 106 671 | K13 taux de commande, K14 panier moyen, K15 taux d'annulation |
| `fait_session` | Une session | 296 166 | K12 sessions par table, K13 entonnoir |
| `fait_abonnement_mensuel` | Un établissement × un mois | 4 707 | K01 à K06 : actifs, MRR, ARR, mouvements, résiliation, cohortes |
| `fait_facturation` | Une facture | 3 549 | K16 CA facturé et encaissé, K17 retards et impayés |
| `fait_marketing` | Une campagne × un jour | 2 868 | K09 CAC, K11 coût par clic |
| `fait_prospect` | Un prospect | 2 246 | K07 conversion, K08 délai de signature |
| `fait_ticket_support` | Un ticket | 952 | K18 délai de résolution et satisfaction |

| Dimension | Lignes | Remarque |
|---|---:|---|
| `dim_date` | 1 096 | Calendrier 2024 à 2026, jours fériés, ramadan |
| `dim_heure` | 24 | Moment de la journée : matin 6 h à 10 h, midi 11 h à 14 h, après-midi 15 h à 18 h, soir 19 h à 22 h, nuit (convention du projet) |
| `dim_etablissement` | 403 | Ville, canal et formules dénormalisés ; état au 31/12/2026 |
| `dim_article` | 14 107 | Prix historisés (SCD2) : une ligne par article et par période de prix ; chaque ligne de commande pointe vers le prix en vigueur le jour de la commande |
| `dim_categorie`, `dim_table`, `dim_ville`, `dim_canal`, `dim_formule` | | Reprises du staging |

**Écarts avec le modèle de la phase 0 (décision D-34) :**
- Trois faits ont été ajoutés : `fait_commande` (46 commandes n'ont plus de ligne valide mais comptent dans les taux), `fait_prospect` et `fait_ticket_support` (KPI K07, K08 et K18, qui n'avaient pas de fait).
- `fait_session` porte la formule de l'établissement le jour de la session : la formule Essentiel ne permet pas de commander, et l'entonnoir doit pouvoir l'exclure.

**Snapshot `snp_etablissements` (décision D-34).** Il garde l'historique des changements de nom, de statut, de formule, de périodicité, de nombre de tables et de date de résiliation (stratégie `check` de dbt).
- Le jeu de données est figé au 31/12/2026 : le premier lancement crée une version par établissement (403), et les lancements suivants n'ajoutent rien. L'historique se remplira quand de nouvelles extractions arriveront (phase 5).
- `dbt_valid_from` et `dbt_valid_to` sont les dates des lancements de dbt, pas les dates métier des changements. Les dates métier restent dans les abonnements (SCD2 de la source).
- Testé sur l'environnement de test : un changement de formule simulé ferme l'ancienne version et en ouvre une nouvelle.

## 6. Tests DQ et validation (T4.4)

**Tests DQ-01 à DQ-27.** Un test par règle du catalogue, dans `tests/dq/`, sur les modèles finaux (marts et intermediate). Chaque test renvoie les lignes en violation ; il passe s'il n'en renvoie aucune. Les 27 passent à 0 violation, avec trois périmètres à connaître :
- **DQ-03 et DQ-13** ne portent pas sur les commandes dont une ligne est en quarantaine, ni, pour DQ-13, sur les sessions dont un événement est en quarantaine : leurs lignes valides sont incomplètes par construction.
- **DQ-12 :** les 11 sessions dont la commande, envoyée entre le 27 et le 31/12/2026, n'est pas reçue (décision D-32) sont marquées `commande_non_recue` dans `fait_session` et comptées à part. Une commande non reçue hors des 5 derniers jours (variable `fenetre_retard_jours`) reste une violation.
- Les tests ont été vérifiés en cassant exprès une valeur pour DQ-03, DQ-15, DQ-18 et DQ-26 : chacun a signalé l'erreur.

**Contrôle final**, après `build` :

```powershell
python 05_dbt/controler_entrepot.py
```

Le script écrit `05_dbt/rapport_validation.md` :
1. **Anomalies retrouvées (jalon J5)**, si le corrigé `solutions/anomalies_injectees.csv` est sur le poste (il n'est pas publié, décision D-16). Une anomalie est retrouvée si sa valeur est dans `qualite.corrections` ou sa ligne dans `qualite.quarantaine`.
2. **Comparaison avec la référence** : chaque table de `donnees_reference/` est comparée, valeur par valeur, au modèle final qui lui correspond.

**Documentation dbt :** `python 05_dbt/lancer_dbt.py docs generate`, puis `python 05_dbt/lancer_dbt.py docs serve`. Le site montre chaque modèle, ses colonnes, ses tests et le graphe de lignage de `raw` jusqu'aux marts. Il n'est pas versionné : le fichier généré contient le chemin complet du dossier du projet sur le poste. Sa publication est prévue en phase 9.

## 7. Résultats vérifiés (25/11/2026, environnement de test)

```sql
-- bilan par table et par règle
SELECT * FROM qualite.bilan_qualite WHERE nb_lignes > 0;
```

| Élément | Valeur |
|---|---|
| Lignes brutes | 2 015 451 |
| Lignes en staging | 1 997 548 |
| Lignes en quarantaine | 17 903 : 17 265 doublons (DQ-29), 383 identifiants inconnus (DQ-02), 240 quantités non positives (DQ-05), 15 dépenses (DQ-23) |
| Valeurs corrigées | 13 788 : 12 266 en staging, 1 522 en intermediate (1 304 horloges, 212 totaux de commande, 6 fusions) |
| Sessions | 296 166, identiques à la référence sauf 29 fins de session (horloges non corrigeables exactement) |
| MRR HT fin d'année | 2 490 DT (2024), 5 125 DT (2025), 8 510 DT (2026), 265 établissements abonnés fin 2026 |
| Tests dbt | 285 éléments, 0 erreur, dont 215 tests : 41 unicités, 52 valeurs obligatoires, 74 clés étrangères, 14 listes de valeurs, 34 tests propres au projet (dont les 27 règles DQ) |
| Règles DQ-01 à DQ-27 | 0 violation |

**Comparaison avec la couche de référence** (faite hors de dbt, avec le corrigé non publié) : après l'étage intermediate, les données sont identiques à la référence, valeur par valeur, sauf sur ces points :
- ce que la source ne permet pas de retrouver : secondes des 1 067 dates au format français, 517 modes de règlement et 10 catégories vides, 18 horloges décalées restées dans l'ordre, 1 total de commande dont une ligne est en quarantaine ;
- les lignes en quarantaine (15 dépenses, 120 lignes et 263 événements à identifiant inconnu, 240 lignes à quantité non positive) ;
- les 11 commandes en retard non livrées (décision D-32).

**99,91 % des 31 718 anomalies injectées sont retrouvées (31 690)**, pour un critère J5 de 95 %. Les 28 autres : 9 noms de plats dont la valeur brute est déjà correcte, 18 horloges dont le décalage laisse l'événement dans l'ordre, 1 total de commande dont une ligne est en quarantaine. Détail : `rapport_validation.md`.

## 8. Fichiers

| Fichier | Rôle |
|---|---|
| `dbt_project.yml` | Configuration du projet : schémas, matérialisations, variables (date d'arrêté, panne, seuil des millimes, fuseau) |
| `profiles.yml` | Connexion à `menuscan_dwh` ; le mot de passe vient de `.env` |
| `lancer_dbt.py` | Lance dbt avec les variables de `.env` |
| `.gitignore` | Exclut `target/` et `logs/` (fichiers générés par dbt) |
