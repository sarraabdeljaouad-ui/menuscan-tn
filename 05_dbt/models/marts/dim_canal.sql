-- Dimension canal d'acquisition.
select canal_id, nom_canal, type_canal, taux_conversion_cible
from {{ ref('stg_canaux_acquisition') }}
