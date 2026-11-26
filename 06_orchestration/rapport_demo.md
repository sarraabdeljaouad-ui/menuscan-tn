# Démonstration mensuelle : comparaison avec l'entrepôt chargé d'un coup

**Généré le :** 26/11/2026 à 16:08 par `06_orchestration/demo/comparer_bases.py`.

Base `menuscan_demo` (36 mois livrés un par un) comparée à `menuscan_dwh` (36 mois chargés d'un coup), table par table : nombre de lignes et empreinte MD5 du contenu complet.

**Résultat : IDENTIQUES** (20 tables comparées).

| Table | Lignes (menuscan_dwh) | Lignes (démonstration) | Contenu |
|---|---:|---:|---|
| `marts.dim_article` | 14107 | 14107 | identique |
| `marts.dim_canal` | 5 | 5 | identique |
| `marts.dim_categorie` | 2735 | 2735 | identique |
| `marts.dim_date` | 1096 | 1096 | identique |
| `marts.dim_etablissement` | 403 | 403 | identique |
| `marts.dim_formule` | 3 | 3 | identique |
| `marts.dim_heure` | 24 | 24 | identique |
| `marts.dim_table` | 7151 | 7151 | identique |
| `marts.dim_ville` | 8 | 8 | identique |
| `marts.fait_abonnement_mensuel` | 4707 | 4707 | identique |
| `marts.fait_commande` | 106671 | 106671 | identique |
| `marts.fait_facturation` | 3549 | 3549 | identique |
| `marts.fait_ligne_commande` | 239353 | 239353 | identique |
| `marts.fait_marketing` | 2868 | 2868 | identique |
| `marts.fait_prospect` | 2246 | 2246 | identique |
| `marts.fait_session` | 296166 | 296166 | identique |
| `marts.fait_ticket_support` | 952 | 952 | identique |
| `qualite.bilan_qualite` | 39 | 39 | identique |
| `qualite.corrections` | 13788 | 13788 | identique |
| `qualite.quarantaine` | 17903 | 17903 | identique |
