# Rapport de chargement de la base applicative

**Date :** 24/11/2026 15:14 · **Base :** menuscan_app, schéma menuscan · **Source :** `donnees_reference` · **Durée :** 71 s

## Tables chargées

| Table | Fichiers | Lignes dans les fichiers | Lignes en base | Statut |
|---|---:|---:|---:|---|
| dim_calendrier | 1 | 1 096 | 1 096 | Conforme |
| ref_villes | 1 | 8 | 8 | Conforme |
| formules | 1 | 3 | 3 | Conforme |
| canaux_acquisition | 1 | 5 | 5 | Conforme |
| campagnes_marketing | 1 | 134 | 134 | Conforme |
| marketing_depenses_quotidiennes | 1 | 2 883 | 2 883 | Conforme |
| prospects | 1 | 2 246 | 2 246 | Conforme |
| etablissements | 1 | 403 | 403 | Conforme |
| abonnements | 1 | 444 | 444 | Conforme |
| factures | 1 | 3 549 | 3 549 | Conforme |
| paiements | 1 | 3 596 | 3 596 | Conforme |
| tickets_support | 1 | 952 | 952 | Conforme |
| categories_menu | 1 | 2 735 | 2 735 | Conforme |
| articles | 1 | 10 717 | 10 717 | Conforme |
| articles_prix_historique | 1 | 14 107 | 14 107 | Conforme |
| tables_salle | 1 | 7 151 | 7 151 | Conforme |
| sessions | 1 | 296 166 | 296 166 | Conforme |
| evenements | 36 | 1 601 767 | 1 601 767 | Conforme |
| commandes | 1 | 106 682 | 106 682 | Conforme |
| lignes_commande | 1 | 239 732 | 239 732 | Conforme |
| **Total** | 55 | 2 294 376 | 2 294 376 | |

## Contrôles qualité

| Règle | Objet | Violations |
|---|---|---:|
| DQ-01 | commandes | 0 |
| DQ-01 | lignes_commande | 0 |
| DQ-01 | sessions | 0 |
| DQ-01 | evenements | 0 |
| DQ-01 | factures | 0 |
| DQ-02 | lignes_commande.article_id | 0 |
| DQ-02 | evenements.session_id | 0 |
| DQ-02 | prospects.etablissement_id | 0 |
| DQ-03 | commandes | 0 |
| DQ-04 | lignes_commande | 0 |
| DQ-05 | lignes_commande | 0 |
| DQ-06 | lignes_commande | 0 |
| DQ-09 | commandes | 0 |
| DQ-11 | evenements | 0 |
| DQ-12 | sessions | 0 |
| DQ-14 | abonnements | 0 |
| DQ-15 | factures | 0 |
| DQ-18 | paiements | 0 |
| DQ-21 | prospects | 0 |
| DQ-23 | marketing_depenses_quotidiennes | 0 |
| DQ-24 | articles_prix_historique | 0 |
| DQ-26 | sessions | 0 |
| DQ-27 | evenements | 0 |

**Résultat : conforme** (20 tables sur 20 conformes, 23 contrôles sur 23 à 0).
