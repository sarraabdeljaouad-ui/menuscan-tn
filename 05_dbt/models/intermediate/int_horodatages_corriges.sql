-- Horloges d'appareil décalées (DQ-37). Dans une session, les identifiants d'événements suivent l'ordre d'émission.
-- Un événement horodaté avant un événement émis plus tôt est « hors rang » : l'horloge du téléphone a reculé.
-- Correction : on l'avance du plus petit nombre de minutes entières qui le replace entre ses voisins.
-- Base : événements gardés en staging et événements écartés seulement pour article inconnu (DQ-02),
-- qui ont bien eu lieu et comptent pour l'ordre de la session. Les doublons (DQ-29) sont exclus.
with base as (
    select evenement_id, session_id, horodatage
    from {{ ref('prep_evenements') }}
    where _regle_rejet is null or _regle_rejet = 'DQ-02'
),
voisins as (
    select *,
        max(horodatage) over (partition by session_id order by evenement_id rows between unbounded preceding and 1 preceding) as precedent,
        min(horodatage) over (partition by session_id order by evenement_id rows between 1 following and unbounded following) as suivant
    from base
),
hors_rang as (
    select * from voisins where horodatage < precedent
)
select
    h.evenement_id, h.session_id, h.horodatage as horodatage_source,
    h.horodatage + m.minutes * interval '1 minute' as horodatage_corrige,
    m.minutes as minutes_decalage,
    h.precedent, h.suivant
from hors_rang h
cross join lateral (
    -- le suivant n'est pas pris en compte s'il est lui-même avant le précédent (deux événements décalés)
    select min(n) as minutes from generate_series(1, 60) n
    where h.horodatage + n * interval '1 minute' >= h.precedent
      and (h.suivant is null or h.suivant < h.precedent or h.horodatage + n * interval '1 minute' <= h.suivant)
) m
