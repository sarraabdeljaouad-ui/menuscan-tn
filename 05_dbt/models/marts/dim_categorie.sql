-- Dimension catégorie de menu.
select categorie_id, etablissement_id, nom_categorie, ordre_affichage
from {{ ref('stg_categories_menu') }}
