-- Dimension article à prix historisés (SCD2) : une ligne par article et par période de prix. Clé : prix_id.
-- Les faits de vente pointent vers la version de prix en vigueur le jour de la commande.
select
    p.prix_id, a.article_id, a.etablissement_id, a.categorie_id, c.nom_categorie, a.nom_article,
    a.statut_article, a.date_ajout, a.date_retrait,
    p.date_debut as valide_du, p.date_fin as valide_au, p.prix_ttc, p.motif_changement, p.est_prix_actuel
from {{ ref('stg_articles_prix_historique') }} p
join {{ ref('stg_articles') }} a on a.article_id = p.article_id
left join {{ ref('stg_categories_menu') }} c on c.categorie_id = a.categorie_id
