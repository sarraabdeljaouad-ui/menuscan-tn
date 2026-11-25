-- DQ-07 : article commandé du même établissement que la commande et proposé à la date de la commande.
select l.ligne_id from {{ ref('fait_ligne_commande') }} l
join {{ ref('fait_commande') }} c using (commande_id)
join {{ ref('stg_articles') }} a on a.article_id = l.article_id
where a.etablissement_id <> c.etablissement_id
   or c.date_heure_commande::date < a.date_ajout
   or (a.date_retrait is not null and c.date_heure_commande::date > a.date_retrait)
