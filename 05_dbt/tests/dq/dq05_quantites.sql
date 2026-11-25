-- DQ-05 : quantités strictement positives.
select ligne_id as identifiant from {{ ref('fait_ligne_commande') }} where quantite <= 0
union all
select evenement_id from {{ ref('int_evenements') }} where quantite <= 0
