# 04_ingestion : chargement de la couche brute (phase 3)

**Auteure :** Sarra Abdeljaouad · **Date :** 25/11/2026 · **Tâches :** T3.1 et T3.2

Ce dossier charge les **124 fichiers bruts** du jeu complet (`menuscan_dataset/donnees_brutes/`, Release `v1.1-donnees`) dans le schéma `raw` de la base `menuscan_dwh`.

**Règle : rien n'est corrigé.** Chaque fichier est chargé tel qu'il est arrivé, anomalies comprises (doublons, montants en millimes, dates au format français, libellés anglais, horloges décalées...). Le nettoyage se fait en phase 4, avec dbt.

## Lancer l'ingestion

Depuis la racine du dépôt, environnement Python activé, Docker lancé, jeu complet décompressé à la racine :

```powershell
python 04_ingestion/ingerer.py
```

| Option | Effet |
|---|---|
| (aucune) | Charge les fichiers nouveaux ou modifiés ; saute ceux déjà chargés et inchangés |
| `--reinitialiser` | Supprime le schéma `raw` (données et journal) puis recharge tout |
| `--seulement tracking` | Ne traite que les fichiers dont le chemin contient « tracking » |
| `--source <dossier>` | Autre emplacement du dossier `donnees_brutes` |

Durée mesurée : 22 secondes pour le chargement complet (2 015 451 lignes) sur l'environnement de test. La base `menuscan_dwh` pèse ensuite environ 600 Mo, surtout à cause des événements stockés en JSONB.

## Fichiers

| Fichier | Rôle |
|---|---|
| `ingerer.py` | Script principal : liste des sources, journal, chargement fichier par fichier |
| `journal.sql` | Schéma `raw`, table `raw.chargements` (journal), table `raw.rejets` |
| `chargeurs/csv_standard.py` | CSV séparés par des virgules |
| `chargeurs/csv_francais.py` | CSV au format français : point-virgule, virgule décimale, dates JJ/MM/AAAA |
| `chargeurs/json_compresse.py` | Journaux de tracking : une ligne JSON par événement, gzip, UTC, libellés anglais |
| `chargeurs/json_api.py` | Export de l'API de paiement : une ligne JSON par paiement, montant imbriqué |

## Tables du schéma raw

Une table par source, nommée d'après le système et l'entité. Les 36 fichiers mensuels d'une même source vont dans une seule table.

| Table | Fichiers | Format |
|---|---|---|
| `raw.backoffice_abonnements`, `_etablissements`, `_formules`, `_tables_salle` | `backoffice/` (4) | CSV |
| `raw.crm_prospects` | `crm/prospects.csv` | CSV |
| `raw.facturation_factures` | `facturation/factures.csv` | CSV français |
| `raw.marketing_campagnes` | `marketing/campagnes_marketing.csv` | CSV |
| `raw.marketing_depenses_quotidiennes` | `marketing/depenses_quotidiennes.csv` | CSV français |
| `raw.menus_articles`, `_articles_prix_historique`, `_categories` | `menus/` (3) | CSV |
| `raw.paiements_api_paiements` | `paiements_api/paiements.jsonl` | JSON d'API |
| `raw.referentiels_calendrier`, `_canaux_acquisition`, `_villes` | `referentiels/` (3) | CSV |
| `raw.support_tickets` | `support/tickets_support.csv` | CSV |
| `raw.tracking_events` | `tracking/events_AAAA_MM.jsonl.gz` (36) | JSON compressé |
| `raw.ventes_commandes` | `ventes/commandes/commandes_AAAA_MM.csv` (36) | CSV |
| `raw.ventes_lignes_commande` | `ventes/lignes_commande/lignes_commande_AAAA_MM.csv` (36) | CSV |

Il n'y a pas de table `sessions` : les systèmes sources n'en livrent pas, elle sera reconstruite en phase 4 à partir des événements.

**Colonnes :**
- **CSV :** une colonne `TEXT` par colonne du fichier, avec le nom de l'en-tête. Aucune valeur n'est convertie (`150,0` reste `150,0`). Une case vide devient `NULL`, le CSV ne distinguant pas « vide » et « absent ».
- **JSON :** une colonne `donnees` (`JSONB`) qui contient la ligne entière. Les clés et les valeurs sont gardées ; seuls l'ordre des clés et les espaces ne sont pas conservés par le type JSONB.
- **Colonnes techniques**, dans chaque table : `_lot_id` (lancement de `ingerer.py`), `_fichier` (chemin relatif dans `donnees_brutes/`), `_ligne` (numéro de ligne dans le fichier), `_charge_le` (heure de chargement, UTC).
- Si un nouveau fichier apporte une colonne inconnue, elle est ajoutée à la table en `TEXT` (dérive de schéma) au lieu de faire échouer le chargement.

## Journal, rechargement et rejets

- **`raw.chargements`** : une ligne par fichier et par lancement. Elle contient l'empreinte SHA-256, la taille, les lignes lues, écrites et rejetées, la durée, le statut (`charge`, `recharge`, `deja_charge`, `echec`) et le message d'erreur.
- **Pas de doublon :** un fichier dont l'empreinte n'a pas changé depuis le dernier chargement réussi est sauté. Un fichier modifié est rechargé : ses anciennes lignes et ses anciens rejets sont supprimés, puis remplacés.
- **Un fichier, une transaction :** si un fichier échoue, il est annulé et journalisé en `echec`. Les autres fichiers continuent, et le script se termine avec un code d'erreur.
- **`raw.rejets`** : les lignes illisibles (nombre de colonnes inattendu, JSON invalide), avec le fichier, le numéro de ligne, le motif et le contenu d'origine. Le jeu v1.1 n'en produit aucune.

```sql
-- dernier état de chaque fichier
SELECT DISTINCT ON (fichier) fichier, statut, lignes_lues, lignes_ecrites, lignes_rejetees, duree_s
FROM raw.chargements ORDER BY fichier, chargement_id DESC;
```

## Contrôler les volumes (T3.2)

```powershell
python 04_ingestion/controler.py
```

Le script fait deux contrôles et écrit le rapport `04_ingestion/rapport_ingestion.md` :

1. **Volumes (bloquant).** Chaque fichier est recompté avec un autre lecteur que celui de l'ingestion (pandas pour les CSV, comptage des lignes pour les JSON). Il est conforme si son empreinte est celle du dernier chargement réussi et si : enregistrements dans le fichier = lignes lues = lignes écrites + lignes rejetées ; lignes écrites = lignes en base ; lignes rejetées = lignes de `raw.rejets`. Au moindre écart, le script se termine avec un code d'erreur.
2. **Rapprochement avec la couche de référence (informatif).** Si `donnees_reference/` est présent, chaque table raw est comparée à sa table de référence par identifiant : lignes en double, identifiants absents du brut ou de la référence. Ces écarts viennent des anomalies volontaires du jeu ; ils sont traités en phase 4.

Durée mesurée : 6 secondes sur l'environnement de test.

**Écart connu :** 11 commandes du 27 au 31/12/2026 et leurs 19 lignes sont dans la référence mais dans aucun fichier brut. Ce sont des commandes en retard qui seraient arrivées dans l'extraction de janvier 2027, qui n'existe pas. Ce n'est pas une perte au chargement (décision D-32, note `09_recette/4-Note de validation de l'ingestion.docx`).

## Vérifications faites (25/11/2026)

- Les 124 fichiers sont chargés sans échec : 2 015 451 lignes.
- Pour chaque fichier, le nombre d'enregistrements compté directement dans le fichier est égal au nombre de lignes lues, au nombre de lignes écrites et au nombre de lignes en base : aucun écart.
- Une relance saute les 124 fichiers (aucune ligne écrite).
- Un fichier modifié est rechargé sans doublon ; une ligne avec une colonne de trop et une ligne JSON tronquée partent dans `raw.rejets` avec leur contenu.
