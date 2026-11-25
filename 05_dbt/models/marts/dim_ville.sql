-- Dimension ville.
select ville_id, ville, gouvernorat, region, est_cotiere, poids_marche, date_ouverture_commerciale
from {{ ref('stg_ref_villes') }}
