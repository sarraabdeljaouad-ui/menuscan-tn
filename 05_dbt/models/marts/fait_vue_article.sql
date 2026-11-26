-- Fait vue d'article : nombre de fiches article ouvertes, par établissement, article, jour et heure (TB-6, D5).
-- prix_id = version de prix en vigueur le jour de la vue, comme pour fait_ligne_commande.
select
    e.etablissement_id, e.article_id, p.prix_id,
    {{ date_id('e.horodatage') }} as date_id, extract(hour from e.horodatage)::smallint as heure,
    count(*) as nb_vues,
    count(distinct e.session_id) as nb_sessions
from {{ ref('int_evenements') }} e
left join {{ ref('stg_articles_prix_historique') }} p
  on p.article_id = e.article_id and e.horodatage::date between p.date_debut and coalesce(p.date_fin, '9999-12-31')
where e.type_evenement = 'vue_article'
group by 1, 2, 3, 4, 5
