-- Dimension date : un jour par ligne, du 01/01/2024 au 31/12/2026. Clé date_id = AAAAMMJJ.
select
    {{ date_id('"date"') }} as date_id, "date", annee, trimestre, mois, nom_mois,
    date_trunc('month', "date")::date as premier_jour_mois, to_char("date", 'YYYY-MM') as annee_mois,
    semaine_iso, jour_semaine, nom_jour, est_weekend, est_jour_ferie, nom_jour_ferie, est_ramadan, periode_activite
from {{ ref('stg_dim_calendrier') }}
