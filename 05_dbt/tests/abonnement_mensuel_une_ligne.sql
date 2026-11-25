-- fait_abonnement_mensuel : une seule ligne par établissement et par mois.
select etablissement_id, mois from {{ ref('fait_abonnement_mensuel') }} group by 1, 2 having count(*) > 1
