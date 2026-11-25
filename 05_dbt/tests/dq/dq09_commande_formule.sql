-- DQ-09 : commande seulement sous formule Commande ou Pro (formule active le jour de la commande).
select c.commande_id from {{ ref('fait_commande') }} c
left join {{ ref('stg_abonnements') }} a on a.etablissement_id = c.etablissement_id
  and c.date_heure_commande::date between a.date_debut and coalesce(a.date_fin, '9999-12-31')
left join {{ ref('dim_formule') }} f on f.formule_id = a.formule_id
where f.inclut_commande is distinct from true
