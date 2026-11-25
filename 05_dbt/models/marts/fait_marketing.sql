-- Fait marketing : une campagne x un jour (dépense, impressions, clics, prospects).
select
    d.depense_id, d.campagne_id, c.canal_id, c.ville_id_cible as ville_id, {{ date_id('d.date') }} as date_id,
    d.depense_ttc, d.impressions, d.clics, d.nb_prospects
from {{ ref('stg_marketing_depenses_quotidiennes') }} d
join {{ ref('stg_campagnes_marketing') }} c on c.campagne_id = d.campagne_id
