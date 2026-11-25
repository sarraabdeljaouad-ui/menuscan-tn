-- DQ-13 : ajouts - retraits du panier = quantités des lignes, par commande et par article.
-- Hors commandes incomplètes (ligne en quarantaine) et sessions dont un événement est en quarantaine (article inconnu).
with panier as (
    select session_id, article_id, sum(case when type_evenement = 'ajout_panier' then quantite else -quantite end) as q
    from {{ ref('int_evenements') }} where type_evenement in ('ajout_panier', 'retrait_panier') group by 1, 2
),
lignes as (select session_id, article_id, sum(quantite) as q from {{ ref('fait_ligne_commande') }} group by 1, 2),
exclues as (
    select session_id from {{ ref('fait_commande') }} where not lignes_completes
    union select contenu->>'session_id' from {{ ref('quarantaine') }} where table_source = 'evenements' and regle_dq <> 'DQ-29'
)
select l.session_id, l.article_id, l.q as quantite_lignes, p.q as quantite_panier
from lignes l left join panier p using (session_id, article_id)
where l.session_id not in (select session_id from exclues) and p.q is distinct from l.q
