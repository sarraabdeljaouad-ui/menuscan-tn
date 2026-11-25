-- Corrections faites à l'étage intermediate, au même format que qualite.corrections.
select 'evenements'::text as table_source, evenement_id as identifiant, 'DQ-37' as regle_dq, 'horodatage' as colonne,
       horodatage_source::text as valeur_avant, horodatage_corrige::text as valeur_apres
from {{ ref('int_horodatages_corriges') }}
where evenement_id in (select evenement_id from {{ ref('stg_evenements') }})
union all
select 'commandes', commande_id, 'DQ-03', 'montant_total_ttc', montant_total_source::text, montant_total_ttc::text
from {{ ref('int_commandes') }} where total_recalcule
union all
select 'etablissements', ancien_id, 'DQ-30', 'etablissement_id', ancien_id, nouvel_id
from {{ ref('int_correspondance_etablissements') }}
