-- Historique des prix. Source : menus/articles_prix_historique.csv. Correction : prix en millimes (DQ-33).
with source as (
    select *, {{ rang_doublon('prix_id') }} as _rang from {{ source('raw', 'menus_articles_prix_historique') }}
)
select
    prix_id, article_id, date_debut::date as date_debut, date_fin::date as date_fin,
    {{ dinars('prix_ttc') }}::numeric(10, 3) as prix_ttc, motif_changement, est_prix_actuel::boolean as est_prix_actuel,
    _fichier, _ligne,
    {{ corrections([corr('DQ-33', 'prix_ttc', est_millimes('prix_ttc'), 'prix_ttc', dinars('prix_ttc'))]) }} as _corrections,
    {{ rejet('prix_id') }}
from source
