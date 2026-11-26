# Rapport de validation de l'entrepôt

**Généré le :** 26/11/2026 à 14:24 par `05_dbt/controler_entrepot.py`, après `dbt build`.

## 1. Anomalies retrouvées (jalon J5)

**31 690 anomalies retrouvées sur 31 718, soit 99,91 %.** Critère du jalon J5 : au moins 95 % (atteint).

Une anomalie est retrouvée si sa valeur a été corrigée pour sa règle (`qualite.corrections`) ou si sa ligne a été écartée (`qualite.quarantaine`).

| Règle | Type d'anomalie | Table | Injectées | Retrouvées | Taux |
|---|---|---|---:|---:|---:|
| DQ-02 | cle_etrangere_orpheline | evenements | 263 | 263 | 100,0 % |
| DQ-02 | cle_etrangere_orpheline | lignes_commande | 120 | 120 | 100,0 % |
| DQ-03 | montant_incoherent | commandes | 213 | 212 | 99,5 % |
| DQ-05 | quantite_non_positive | lignes_commande | 240 | 240 | 100,0 % |
| DQ-15 | montant_incoherent | factures | 18 | 18 | 100,0 % |
| DQ-23 | clics_superieurs_aux_impressions | marketing_depenses_quotidiennes | 10 | 10 | 100,0 % |
| DQ-23 | montant_negatif | marketing_depenses_quotidiennes | 5 | 5 | 100,0 % |
| DQ-28 | format_date_non_iso | commandes | 1 067 | 1 067 | 100,0 % |
| DQ-29 | doublon_ingestion | articles | 32 | 32 | 100,0 % |
| DQ-29 | doublon_ingestion | commandes | 427 | 427 | 100,0 % |
| DQ-29 | doublon_ingestion | evenements | 16 018 | 16 018 | 100,0 % |
| DQ-29 | doublon_ingestion | factures | 11 | 11 | 100,0 % |
| DQ-29 | doublon_ingestion | lignes_commande | 719 | 719 | 100,0 % |
| DQ-29 | doublon_ingestion | paiements | 36 | 36 | 100,0 % |
| DQ-29 | doublon_ingestion | prospects | 22 | 22 | 100,0 % |
| DQ-30 | doublon_metier_etablissement | etablissements | 6 | 6 | 100,0 % |
| DQ-31 | email_invalide | etablissements | 6 | 6 | 100,0 % |
| DQ-31 | format_telephone_non_normalise | etablissements | 16 | 16 | 100,0 % |
| DQ-31 | format_telephone_non_normalise | prospects | 90 | 90 | 100,0 % |
| DQ-32 | libelle_non_normalise | abonnements | 13 | 13 | 100,0 % |
| DQ-32 | libelle_non_normalise | articles | 214 | 205 | 95,8 % |
| DQ-32 | libelle_non_normalise | commandes | 2 133 | 2 133 | 100,0 % |
| DQ-32 | libelle_non_normalise | etablissements | 12 | 12 | 100,0 % |
| DQ-32 | libelle_non_normalise | prospects | 67 | 67 | 100,0 % |
| DQ-32 | libelle_non_normalise | tickets_support | 38 | 38 | 100,0 % |
| DQ-33 | montant_en_millimes | articles_prix_historique | 42 | 42 | 100,0 % |
| DQ-33 | montant_en_millimes | lignes_commande | 240 | 240 | 100,0 % |
| DQ-33 | montant_en_millimes | paiements | 72 | 72 | 100,0 % |
| DQ-35 | arrivee_tardive | commandes | 148 | 148 | 100,0 % |
| DQ-35 | arrivee_tardive | evenements | 7 566 | 7 566 | 100,0 % |
| DQ-37 | horloge_appareil_decalee | evenements | 1 323 | 1 305 | 98,6 % |
| DQ-38 | champ_obligatoire_vide | commandes | 517 | 517 | 100,0 % |
| DQ-38 | champ_obligatoire_vide | etablissements | 4 | 4 | 100,0 % |
| DQ-38 | champ_obligatoire_vide | tickets_support | 10 | 10 | 100,0 % |

*Corrigé absent de ce poste (non publié, décision D-16) : la mesure ci-dessus est celle du dernier poste qui l'avait.*

*Corrigé absent de ce poste (non publié, décision D-16) : la mesure ci-dessus est celle du dernier poste qui l'avait.*

*Corrigé absent de ce poste (non publié, décision D-16) : la mesure ci-dessus est celle du dernier poste qui l'avait.*

## 2. Comparaison avec la couche de référence

Chaque table de `donnees_reference/` est comparée au modèle final qui lui correspond, sur l'identifiant et sur chaque colonne commune. Un écart est une valeur différente après normalisation des formats (nombres à 3 décimales, dates).

| Référence | Modèle de l'entrepôt | Lignes référence | Lignes entrepôt | Absentes de l'entrepôt | En plus | Colonnes comparées | Valeurs différentes |
|---|---|---:|---:|---:|---:|---:|---|
| dim_calendrier | `staging.stg_dim_calendrier` | 1 096 | 1 096 | 0 | 0 | 12 | aucune |
| ref_villes | `marts.dim_ville` | 8 | 8 | 0 | 0 | 6 | aucune |
| formules | `marts.dim_formule` | 3 | 3 | 0 | 0 | 7 | aucune |
| canaux_acquisition | `marts.dim_canal` | 5 | 5 | 0 | 0 | 3 | aucune |
| campagnes_marketing | `staging.stg_campagnes_marketing` | 134 | 134 | 0 | 0 | 6 | aucune |
| marketing_depenses_quotidiennes | `marts.fait_marketing` | 2 883 | 2 868 | 15 | 0 | 5 | aucune |
| prospects | `marts.fait_prospect` | 2 246 | 2 246 | 0 | 0 | 10 | aucune |
| etablissements | `marts.dim_etablissement` | 403 | 403 | 0 | 0 | 15 | aucune |
| abonnements | `staging.stg_abonnements` | 444 | 444 | 0 | 0 | 8 | aucune |
| factures | `marts.fait_facturation` | 3 549 | 3 549 | 0 | 0 | 14 | aucune |
| paiements | `staging.stg_paiements` | 3 596 | 3 596 | 0 | 0 | 8 | aucune |
| tickets_support | `marts.fait_ticket_support` | 952 | 952 | 0 | 0 | 8 | categorie : 10 |
| categories_menu | `marts.dim_categorie` | 2 735 | 2 735 | 0 | 0 | 3 | aucune |
| articles | `staging.stg_articles` | 10 717 | 10 717 | 0 | 0 | 7 | aucune |
| articles_prix_historique | `staging.stg_articles_prix_historique` | 14 107 | 14 107 | 0 | 0 | 6 | aucune |
| tables_salle | `marts.dim_table` | 7 151 | 7 151 | 0 | 0 | 6 | aucune |
| commandes | `marts.fait_commande` | 106 682 | 106 671 | 11 | 0 | 11 | date_heure_commande : 1 055, montant_total_ttc : 1, mode_reglement : 517 |
| lignes_commande | `marts.fait_ligne_commande` | 239 732 | 239 353 | 379 | 0 | 5 | aucune |
| sessions | `marts.fait_session` | 296 166 | 296 166 | 0 | 0 | 10 | fin_session : 29 |
| evenements | `intermediate.int_evenements` | 1 601 767 | 1 601 504 | 263 | 0 | 6 | horodatage : 29 |

Écarts attendus, expliqués dans `05_dbt/README.md` (§ 7) :
- lignes absentes : lignes en quarantaine (dépenses DQ-23, lignes et événements à identifiant inconnu DQ-02, quantités DQ-05) et 11 commandes en retard non reçues avec leurs 19 lignes (décision D-32) ;
- valeurs différentes : secondes perdues des dates au format français (DQ-28), modes de règlement et catégories vides remplacés par « non renseigné » (DQ-38), horloges décalées non détectables ou non exactement corrigeables (DQ-37), total d'une commande dont une ligne est en quarantaine (DQ-03).
