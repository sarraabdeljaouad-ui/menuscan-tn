-- Campagnes marketing : typage seul. Source : marketing/campagnes_marketing.csv
with source as (
    select *, {{ rang_doublon('campagne_id') }} as _rang from {{ source('raw', 'marketing_campagnes') }}
)
select
    campagne_id, canal_id, nom_campagne, date_debut::date as date_debut, date_fin::date as date_fin,
    budget_prevu::numeric(10, 3) as budget_prevu, ville_id_cible,
    _fichier, _ligne, '[]'::jsonb as _corrections,
    {{ rejet('campagne_id') }}
from source
