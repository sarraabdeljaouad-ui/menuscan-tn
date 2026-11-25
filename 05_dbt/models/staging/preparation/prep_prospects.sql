-- Prospects du CRM. Source : crm/prospects.csv
-- Corrections : nom d'établissement (DQ-32), téléphone au format +216 (DQ-31).
with source as (
    select *, {{ rang_doublon('prospect_id') }} as _rang from {{ source('raw', 'crm_prospects') }}
),
nettoyee as (
    select
        s.prospect_id, s.date_contact::date as date_contact, s.canal_id, s.campagne_id, s.ville_id, s.type_etablissement,
        coalesce(n.nom_canonique, {{ espaces('s.nom_etablissement') }}) as nom_etablissement,
        {{ telephone('s.telephone') }} as telephone,
        s.statut_prospect, s.date_conversion::date as date_conversion, s.etablissement_id, s.parrain_etablissement_id, s.motif_perte,
        s.nom_etablissement as _nom_brut, s.telephone as _telephone_brut, s._fichier, s._ligne, s._rang
    from source s
    left join {{ ref('prep_noms_etablissements') }} n on n.cle = {{ cle_libelle('s.nom_etablissement') }}
)
select
    prospect_id, date_contact, canal_id, campagne_id, ville_id, type_etablissement, nom_etablissement, telephone,
    statut_prospect, date_conversion, etablissement_id, parrain_etablissement_id, motif_perte,
    _fichier, _ligne,
    {{ corrections([
        corr_si_change('DQ-32', 'nom_etablissement', '_nom_brut', 'nom_etablissement'),
        corr_si_change('DQ-31', 'telephone', '_telephone_brut', 'telephone'),
    ]) }} as _corrections,
    {{ rejet('prospect_id') }}
from nettoyee
