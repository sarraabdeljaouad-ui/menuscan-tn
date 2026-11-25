-- Calendrier : typage seul. Source : referentiels/dim_calendrier.csv
with source as (
    select *, {{ rang_doublon('date') }} as _rang from {{ source('raw', 'referentiels_calendrier') }}
)
select
    date::date as date, annee::smallint as annee, trimestre::smallint as trimestre, mois::smallint as mois,
    nom_mois, semaine_iso::smallint as semaine_iso, jour_semaine::smallint as jour_semaine, nom_jour,
    est_weekend::boolean as est_weekend, est_jour_ferie::boolean as est_jour_ferie, nom_jour_ferie,
    est_ramadan::boolean as est_ramadan, periode_activite,
    _fichier, _ligne, '[]'::jsonb as _corrections,
    {{ rejet('date') }}
from source
