-- Formules : typage seul. Source : backoffice/formules.csv
with source as (
    select *, {{ rang_doublon('formule_id') }} as _rang from {{ source('raw', 'backoffice_formules') }}
)
select
    formule_id, nom_formule, prix_mensuel_ht::numeric(10, 3) as prix_mensuel_ht, inclut_commande::boolean as inclut_commande,
    inclut_statistiques::boolean as inclut_statistiques, description, prix_annuel_ht::numeric(10, 3) as prix_annuel_ht,
    frais_mise_en_place_ht::numeric(10, 3) as frais_mise_en_place_ht,
    _fichier, _ligne, '[]'::jsonb as _corrections,
    {{ rejet('formule_id') }}
from source
