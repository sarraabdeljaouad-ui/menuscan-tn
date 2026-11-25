# Rapport d'ingestion de la couche brute

**Généré le :** 25/11/2026 à 14:48 par `04_ingestion/controler.py` · **Durée :** 10 s

**Source :** `menuscan_dataset\donnees_brutes` · **Base :** `menuscan_dwh`, schéma `raw`

## 1. Synthèse

| Indicateur | Valeur |
|---|---|
| Fichiers contrôlés | 124 |
| Fichiers conformes | 124 |
| Fichiers en écart | 0 |
| Enregistrements comptés dans les fichiers | 2 015 451 |
| Lignes écrites selon le journal | 2 015 451 |
| Lignes présentes dans raw | 2 015 451 |
| Lignes rejetées (raw.rejets) | 0 |
| **Contrôle des volumes** | **CONFORME** |

Un fichier est conforme si son empreinte est celle du dernier chargement réussi et si ces nombres sont égaux : enregistrements recomptés dans le fichier = lignes lues = lignes écrites + lignes rejetées ; lignes écrites = lignes en base ; lignes rejetées = lignes de raw.rejets.

## 2. Volumes par table

| Table raw | Fichiers | Dans les fichiers | Lues | Écrites | En base | Rejets | Fichiers en écart |
|---|---:|---:|---:|---:|---:|---:|---:|
| `raw.backoffice_abonnements` | 1 | 444 | 444 | 444 | 444 | 0 | 0 |
| `raw.backoffice_etablissements` | 1 | 409 | 409 | 409 | 409 | 0 | 0 |
| `raw.backoffice_formules` | 1 | 3 | 3 | 3 | 3 | 0 | 0 |
| `raw.backoffice_tables_salle` | 1 | 7 151 | 7 151 | 7 151 | 7 151 | 0 | 0 |
| `raw.crm_prospects` | 1 | 2 268 | 2 268 | 2 268 | 2 268 | 0 | 0 |
| `raw.facturation_factures` | 1 | 3 560 | 3 560 | 3 560 | 3 560 | 0 | 0 |
| `raw.marketing_campagnes` | 1 | 134 | 134 | 134 | 134 | 0 | 0 |
| `raw.marketing_depenses_quotidiennes` | 1 | 2 883 | 2 883 | 2 883 | 2 883 | 0 | 0 |
| `raw.menus_articles` | 1 | 10 749 | 10 749 | 10 749 | 10 749 | 0 | 0 |
| `raw.menus_articles_prix_historique` | 1 | 14 107 | 14 107 | 14 107 | 14 107 | 0 | 0 |
| `raw.menus_categories` | 1 | 2 735 | 2 735 | 2 735 | 2 735 | 0 | 0 |
| `raw.paiements_api_paiements` | 1 | 3 632 | 3 632 | 3 632 | 3 632 | 0 | 0 |
| `raw.referentiels_calendrier` | 1 | 1 096 | 1 096 | 1 096 | 1 096 | 0 | 0 |
| `raw.referentiels_canaux_acquisition` | 1 | 5 | 5 | 5 | 5 | 0 | 0 |
| `raw.referentiels_villes` | 1 | 8 | 8 | 8 | 8 | 0 | 0 |
| `raw.support_tickets` | 1 | 952 | 952 | 952 | 952 | 0 | 0 |
| `raw.tracking_events` | 36 | 1 617 785 | 1 617 785 | 1 617 785 | 1 617 785 | 0 | 0 |
| `raw.ventes_commandes` | 36 | 107 098 | 107 098 | 107 098 | 107 098 | 0 | 0 |
| `raw.ventes_lignes_commande` | 36 | 240 432 | 240 432 | 240 432 | 240 432 | 0 | 0 |
| **Total** | **124** | **2 015 451** | **2 015 451** | **2 015 451** | **2 015 451** | **0** | **0** |

## 3. Fichiers en écart

Aucun.

## 4. Rapprochement avec la couche de référence

Contrôle informatif : la couche brute contient volontairement des anomalies. Ces écarts ne sont pas des erreurs d'ingestion ; ils seront traités en phase 4 (staging et quarantaine).

| Table raw | Lignes brut | Lignes référence | Identifiants distincts (brut) | Lignes en double | Absents du brut | Absents de la référence |
|---|---:|---:|---:|---:|---:|---:|
| `raw.backoffice_abonnements` | 444 | 444 | 444 | 0 | 0 | 0 |
| `raw.backoffice_etablissements` | 409 | 403 | 409 | 0 | 0 | 6 |
| `raw.backoffice_formules` | 3 | 3 | 3 | 0 | 0 | 0 |
| `raw.backoffice_tables_salle` | 7 151 | 7 151 | 7 151 | 0 | 0 | 0 |
| `raw.crm_prospects` | 2 268 | 2 246 | 2 246 | 22 | 0 | 0 |
| `raw.facturation_factures` | 3 560 | 3 549 | 3 549 | 11 | 0 | 0 |
| `raw.marketing_campagnes` | 134 | 134 | 134 | 0 | 0 | 0 |
| `raw.marketing_depenses_quotidiennes` | 2 883 | 2 883 | 2 883 | 0 | 0 | 0 |
| `raw.menus_articles` | 10 749 | 10 717 | 10 717 | 32 | 0 | 0 |
| `raw.menus_articles_prix_historique` | 14 107 | 14 107 | 14 107 | 0 | 0 | 0 |
| `raw.menus_categories` | 2 735 | 2 735 | 2 735 | 0 | 0 | 0 |
| `raw.paiements_api_paiements` | 3 632 | 3 596 | 3 596 | 36 | 0 | 0 |
| `raw.referentiels_calendrier` | 1 096 | 1 096 | 1 096 | 0 | 0 | 0 |
| `raw.referentiels_canaux_acquisition` | 5 | 5 | 5 | 0 | 0 | 0 |
| `raw.referentiels_villes` | 8 | 8 | 8 | 0 | 0 | 0 |
| `raw.support_tickets` | 952 | 952 | 952 | 0 | 0 | 0 |
| `raw.tracking_events` | 1 617 785 | 1 601 767 | 1 601 767 | 16 018 | 0 | 0 |
| `raw.ventes_commandes` | 107 098 | 106 682 | 106 671 | 427 | 11 | 0 |
| `raw.ventes_lignes_commande` | 240 432 | 239 732 | 239 713 | 719 | 19 | 0 |

- **Lignes en double :** lignes dont l'identifiant figure déjà dans la table (doublons d'ingestion).
- **Absents du brut :** identifiants de la référence qu'aucun fichier ne contient. Exemples pour `ventes_commandes` : CMD0017662, CMD0037970, CMD0037976, CMD0044107, CMD0050825. Exemples pour `ventes_lignes_commande` : LIG0040086, LIG0040087, LIG0085339, LIG0085351, LIG0085352.
- **Absents de la référence :** identifiants présents dans le brut seulement (par exemple un établissement saisi deux fois sous deux identifiants).
- La table `sessions` de la référence n'a pas de source brute : elle sera reconstruite en phase 4 à partir des événements.

## 5. Historique des lancements de l'ingestion

| Lot | Début | Chargés | Rechargés | Inchangés | En échec | Lignes écrites | Durée cumulée (s) |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | 25/11/2026 14:32 | 124 | 0 | 0 | 0 | 2 015 451 | 47.4 |
| 2 | 25/11/2026 14:33 | 0 | 0 | 124 | 0 | 0 | 0.1 |
