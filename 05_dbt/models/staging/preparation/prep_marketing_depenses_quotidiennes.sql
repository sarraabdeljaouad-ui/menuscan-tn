-- Dépenses quotidiennes des campagnes. Source : marketing/depenses_quotidiennes.csv, au format français (DQ-36).
-- Quarantaine : dépense négative, clics supérieurs aux impressions, jour hors de la campagne (DQ-23).
with source as (
    select *, {{ rang_doublon('depense_id') }} as _rang from {{ source('raw', 'marketing_depenses_quotidiennes') }}
),
typee as (
    select
        s.depense_id, s.campagne_id, {{ date_fr('s.date') }} as date, {{ decimal_fr('s.depense_ttc') }}::numeric(10, 3) as depense_ttc,
        s.impressions::integer as impressions, s.clics::integer as clics, s.nb_prospects::integer as nb_prospects,
        s._fichier, s._ligne, s._rang
    from source s
)
select
    t.depense_id, t.campagne_id, t.date, t.depense_ttc, t.impressions, t.clics, t.nb_prospects,
    t._fichier, t._ligne, '[]'::jsonb as _corrections,
    {{ rejet('t.depense_id', [
        ['DQ-23', 't.depense_ttc < 0', 'dépense négative'],
        ['DQ-23', 't.clics > t.impressions', 'clics supérieurs aux impressions'],
        ['DQ-23', 'not (t.date between c.date_debut and c.date_fin)', 'jour hors de la période de la campagne'],
    ]) }}
from typee t
left join {{ ref('prep_campagnes_marketing') }} c on c.campagne_id = t.campagne_id and c._regle_rejet is null
