-- MRR mensuel : une ligne par établissement et par mois, du premier mois d'abonnement au mois qui suit la résiliation.
-- MRR = prix mensuel HT catalogue de l'abonnement actif le dernier jour du mois (abonnés annuels compris),
-- convention du jeu de données. Le mois de mise en service compte, même s'il n'est pas facturé (règles métier, § 4).
-- Mouvement : nouveau, expansion (montée de gamme), contraction (descente), resiliation (MRR à zéro), stable.
with mois as (
    select m::date as mois, (m + interval '1 month' - interval '1 day')::date as fin_mois
    from generate_series(
        (select date_trunc('month', min(date_debut)) from {{ ref('stg_abonnements') }}),
        date_trunc('month', '{{ var("date_arrete") }}'::date), interval '1 month') m
),
grille as (
    select e.etablissement_id, m.mois, m.fin_mois
    from {{ ref('int_etablissements') }} e cross join mois m
),
actif as (
    select g.etablissement_id, g.mois, a.abonnement_id, a.formule_id, a.periodicite, coalesce(a.prix_mensuel_ht, 0) as mrr_ht
    from grille g
    left join {{ ref('stg_abonnements') }} a
      on a.etablissement_id = g.etablissement_id and a.date_debut <= g.fin_mois and (a.date_fin is null or a.date_fin >= g.fin_mois)
),
avec_precedent as (
    select *,
        coalesce(lag(mrr_ht) over (partition by etablissement_id order by mois), 0) as mrr_precedent_ht,
        coalesce(max(mrr_ht) over (partition by etablissement_id order by mois rows between unbounded preceding and 1 preceding), 0) > 0 as deja_abonne
    from actif
)
select
    etablissement_id, mois, abonnement_id, formule_id, periodicite, mrr_ht, mrr_precedent_ht,
    mrr_ht - mrr_precedent_ht as variation_ht,
    case
        when mrr_precedent_ht = 0 and mrr_ht > 0 then case when deja_abonne then 'reactivation' else 'nouveau' end
        when mrr_ht = 0 and mrr_precedent_ht > 0 then 'resiliation'
        when mrr_ht > mrr_precedent_ht then 'expansion'
        when mrr_ht < mrr_precedent_ht then 'contraction'
        else 'stable'
    end as mouvement
from avec_precedent
where mrr_ht > 0 or mrr_precedent_ht > 0
