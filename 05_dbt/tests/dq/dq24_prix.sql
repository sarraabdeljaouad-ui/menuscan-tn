-- DQ-24 : historique des prix contigu, un seul prix en vigueur par article, première période = date d'ajout.
with p as (
    select *, lag(valide_au) over (partition by article_id order by valide_du) as fin_precedente,
           row_number() over (partition by article_id order by valide_du) as rang
    from {{ ref('dim_article') }}
)
select prix_id as identifiant from p where (rang > 1 and valide_du <> fin_precedente + 1) or (rang = 1 and valide_du <> date_ajout)
union all
select article_id from {{ ref('dim_article') }} group by article_id having count(*) filter (where est_prix_actuel) <> 1
