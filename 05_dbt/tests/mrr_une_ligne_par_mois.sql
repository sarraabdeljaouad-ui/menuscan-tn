-- int_mrr_mensuel : une seule ligne par établissement et par mois.
select etablissement_id, mois, count(*) as nb
from {{ ref('int_mrr_mensuel') }}
group by etablissement_id, mois
having count(*) > 1
