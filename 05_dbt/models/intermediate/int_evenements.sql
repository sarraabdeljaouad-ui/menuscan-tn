{{ config(materialized="view") }}
-- Vue et non table : évite de recopier 1,6 million de lignes (environ 300 Mo).
-- Événements valides avec l'horodatage corrigé des horloges décalées (DQ-37).
select
    e.evenement_id, e.session_id, e.etablissement_id, e.table_id,
    coalesce(c.horodatage_corrige, e.horodatage) as horodatage,
    c.evenement_id is not null as horloge_corrigee,
    e.type_evenement, e.article_id, e.quantite, e.appareil, e.langue, e._fichier, e._ligne
from {{ ref('stg_evenements') }} e
left join {{ ref('int_horodatages_corriges') }} c on c.evenement_id = e.evenement_id
