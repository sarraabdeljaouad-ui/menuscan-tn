-- Canaux d'acquisition : typage seul. Source : referentiels/canaux_acquisition.csv
with source as (
    select *, {{ rang_doublon('canal_id') }} as _rang from {{ source('raw', 'referentiels_canaux_acquisition') }}
)
select
    canal_id, nom_canal, type_canal, taux_conversion_cible::numeric(4, 2) as taux_conversion_cible,
    _fichier, _ligne, '[]'::jsonb as _corrections,
    {{ rejet('canal_id') }}
from source
