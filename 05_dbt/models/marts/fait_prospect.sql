-- Fait prospect : une ligne par prospect (conversion, délai de signature).
-- Ajouté au modèle prévu en phase 0 pour couvrir les KPI K07 et K08.
select
    p.prospect_id, p.canal_id, p.campagne_id, p.ville_id, p.type_etablissement,
    {{ date_id('p.date_contact') }} as date_id, p.date_contact, p.date_conversion,
    p.statut_prospect, p.statut_prospect = 'converti' as est_converti,
    p.date_conversion - p.date_contact as delai_conversion_jours,
    coalesce(f.nouvel_id, p.etablissement_id) as etablissement_id, p.parrain_etablissement_id, p.motif_perte
from {{ ref('stg_prospects') }} p
left join {{ ref('int_correspondance_etablissements') }} f on f.ancien_id = p.etablissement_id
