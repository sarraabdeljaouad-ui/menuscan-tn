-- Pont du MRR : pour chaque mois, MRR du mois = MRR du mois précédent + somme des variations.
with par_mois as (
    select mois, sum(mrr_ht) as mrr, sum(variation_ht) as variation from {{ ref('int_mrr_mensuel') }} group by mois
),
pont as (
    select mois, mrr, variation, coalesce(lag(mrr) over (order by mois), 0) as mrr_precedent from par_mois
)
select * from pont where abs(mrr - (mrr_precedent + variation)) > 0.001
