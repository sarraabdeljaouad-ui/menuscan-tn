-- Fait ligne de commande : une ligne par article commandé. prix_id = version de prix en vigueur le jour de la commande.
select
    l.ligne_id, l.commande_id, c.session_id, c.etablissement_id, c.table_id, l.article_id, p.prix_id,
    {{ date_id('c.date_heure_commande') }} as date_id, extract(hour from c.date_heure_commande)::smallint as heure,
    c.statut_commande, c.statut_commande = 'servie' as est_servie,
    l.quantite, l.prix_unitaire_ttc, l.montant_ligne_ttc,
    p.prix_ttc as prix_catalogue_ttc, abs(l.prix_unitaire_ttc - p.prix_ttc) <= 0.001 as prix_conforme
from {{ ref('stg_lignes_commande') }} l
join {{ ref('int_commandes') }} c on c.commande_id = l.commande_id
left join {{ ref('stg_articles_prix_historique') }} p
  on p.article_id = l.article_id and c.date_heure_commande::date between p.date_debut and coalesce(p.date_fin, '9999-12-31')
