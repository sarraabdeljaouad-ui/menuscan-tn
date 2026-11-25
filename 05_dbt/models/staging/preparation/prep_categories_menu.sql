-- Catégories des menus : typage seul. Source : menus/categories_menu.csv
with source as (
    select *, {{ rang_doublon('categorie_id') }} as _rang from {{ source('raw', 'menus_categories') }}
)
select
    categorie_id, etablissement_id, nom_categorie, ordre_affichage::smallint as ordre_affichage,
    _fichier, _ligne, '[]'::jsonb as _corrections,
    {{ rejet('categorie_id') }}
from source
