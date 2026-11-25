-- Villes : typage seul. Source : referentiels/ref_villes.csv
with source as (
    select *, {{ rang_doublon('ville_id') }} as _rang from {{ source('raw', 'referentiels_villes') }}
)
select
    ville_id, ville, gouvernorat, region, est_cotiere::boolean as est_cotiere, poids_marche::numeric(4, 2) as poids_marche,
    date_ouverture_commerciale::date as date_ouverture_commerciale,
    _fichier, _ligne, '[]'::jsonb as _corrections,
    {{ rejet('ville_id') }}
from source
