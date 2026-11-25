-- Dimension établissement : 403 établissements dédoublonnés (DQ-30), avec ville, canal et formules dénormalisés.
-- État au 31/12/2026 ; l'historique des changements est gardé par le snapshot snp_etablissements.
select
    e.etablissement_id, e.nom_etablissement, e.type_etablissement,
    e.ville_id, v.ville, v.gouvernorat, v.region,
    e.canal_id, c.nom_canal, c.type_canal, e.campagne_id, e.prospect_id,
    e.date_signature, e.date_mise_en_service, date_trunc('month', e.date_mise_en_service)::date as mois_cohorte,
    e.nb_tables,
    e.formule_initiale_id, fi.nom_formule as formule_initiale, e.formule_actuelle_id, fa.nom_formule as formule_actuelle,
    e.periodicite_facturation, e.statut_etablissement, e.statut_etablissement = 'actif' as est_actif,
    e.date_resiliation, e.motif_resiliation
from {{ ref('int_etablissements') }} e
left join {{ ref('stg_ref_villes') }} v on v.ville_id = e.ville_id
left join {{ ref('stg_canaux_acquisition') }} c on c.canal_id = e.canal_id
left join {{ ref('stg_formules') }} fi on fi.formule_id = e.formule_initiale_id
left join {{ ref('stg_formules') }} fa on fa.formule_id = e.formule_actuelle_id
